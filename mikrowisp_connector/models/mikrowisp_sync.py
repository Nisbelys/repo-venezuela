import json
import logging
import ssl
import urllib.request

import ijson

from odoo import api, fields, models

from .mikrowisp_estado_log import tipo_movimiento

_logger = logging.getLogger(__name__)

_ESTADOS = ['ACTIVO', 'SUSPENDIDO', 'CORTADO', 'RETIRADO']
_VALID_ESTADOS = set(_ESTADOS)
_VALID_SERVICE_STATUS = {'ONLINE', 'OFFLINE'}

# ACTIVO y SUSPENDIDO suelen tener demasiados registros para que
# GetClientsDetails los devuelva sin que el servidor cierre la conexión a
# medio camino ("Remote end closed connection" / "premature EOF") — pasa en
# todas las zonas observadas hasta ahora, sin importar la versión de
# Mikrowisp. Para esos dos estados se usa GetAllClients paginado en su lugar.
_TIMEOUT_POR_ESTADO = {
    'ACTIVO':     600,
    'SUSPENDIDO': 600,
    'CORTADO':    120,
    'RETIRADO':   300,
}
_ESTADOS_PAGINADOS = {'ACTIVO': 0, 'SUSPENDIDO': 1}
_PAGE_SIZE = 500


class MikrowispSync(models.AbstractModel):
    _name = 'mikrowisp.sync'
    _description = 'Base de sincronización Mikrowisp (compartida entre zonas)'

    _ZONAS = ['caracas', 'llanos', 'puentehierro', 'ocumare']

    _BATCH_SIZE = 100
    _FACTURA_PAGE_SIZE = 100
    # Tras alcanzar facturas ya conocidas, se siguen revisando algunas páginas más
    # por si una factura vieja cambió de estado (ej. vencida que se acaba de pagar).
    _FACTURA_REFRESH_EXTRA_PAGES = 20
    # Tope de seguridad para no quedar en un bucle infinito si la API nunca
    # devuelve una página vacía (500,000 facturas como límite duro).
    _FACTURA_MAX_PAGINAS = 5000

    # -------------------------------------------------------------------------
    # Streaming de la API
    # -------------------------------------------------------------------------

    def _stream_clientes(self, cfg, estado):
        """Genera clientes uno a uno desde la API sin cargar la respuesta entera en RAM."""
        if not cfg['url'] or not cfg['token']:
            raise ValueError('Mikrowisp: configure la URL y el Token API en Ajustes.')

        timeout = _TIMEOUT_POR_ESTADO.get(estado, 300)
        url = f"{cfg['url']}/api/v1/GetClientsDetails"
        payload = json.dumps({'token': cfg['token'], 'estado': estado}).encode()
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(
            url, data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
            for cliente in ijson.items(r, 'datos.item'):
                if cliente.get('id'):
                    yield cliente

    def _stream_clientes_paginado(self, cfg, estado_num):
        """Itera página a página por GetAllClients sin cargar todo en RAM.

        Alternativa a _stream_clientes para estados donde GetClientsDetails
        agota el timeout o corta la conexión a medio camino.
        """
        url = f"{cfg['url']}/api/v1/GetAllClients"
        ctx = ssl._create_unverified_context()
        pagina = 1
        while True:
            payload = json.dumps({
                'token': cfg['token'],
                'estado': estado_num,
                'limit': _PAGE_SIZE,
                'pagina': pagina,
            }).encode()
            req = urllib.request.Request(
                url, data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
                data = json.loads(r.read())

            clientes = data.get('clientes') or []
            for cliente in clientes:
                if cliente.get('id'):
                    # GetAllClients devuelve servicios como entero (conteo),
                    # lo normalizamos a lista vacía para que _build_partner_vals no falle
                    if isinstance(cliente.get('servicios'), int):
                        cliente['servicios'] = []
                    yield cliente

            if len(clientes) < _PAGE_SIZE:
                break
            pagina += 1

    # -------------------------------------------------------------------------
    # Construcción de valores para res.partner
    # -------------------------------------------------------------------------

    def _build_partner_vals(self, cliente, country_ve_id, zona, city):
        servicios = cliente.get('servicios') or []
        svc = servicios[0] if servicios else {}
        facturacion = cliente.get('facturacion') or {}

        estado = (cliente.get('estado') or '').upper()
        svc_status = (svc.get('status_user') or '').upper()

        return {
            'name': cliente.get('nombre') or 'Sin nombre',
            'email': cliente.get('correo') or False,
            'phone': cliente.get('telefono') or cliente.get('movil') or False,
            'street': cliente.get('direccion_principal') or False,
            'city': city,
            'country_id': country_ve_id,
            'customer_rank': 1,
            'is_mikrowisp': True,
            'mikrowisp_zona': zona,
            'mikrowisp_id': cliente.get('id') or 0,
            'mikrowisp_codigo': cliente.get('codigo') or '',
            'mikrowisp_cedula': cliente.get('cedula') or '',
            'mikrowisp_estado': estado if estado in _VALID_ESTADOS else False,
            'mikrowisp_service_status': svc_status if svc_status in _VALID_SERVICE_STATUS else False,
            'mikrowisp_ip': svc.get('ip') or '',
            'mikrowisp_mac': svc.get('mac') or '',
            'mikrowisp_plan': svc.get('perfil') or '',
            'mikrowisp_deuda': float(facturacion.get('total_facturas') or 0),
            'mikrowisp_facturas_nopagadas': int(facturacion.get('facturas_nopagadas') or 0),
            'mikrowisp_last_sync': fields.Datetime.now(),
        }

    # -------------------------------------------------------------------------
    # Upsert por lotes
    # -------------------------------------------------------------------------

    def _write_batch(self, Partner, batch, country_ve_id, zona, city):
        """Upsert de un lote. Incluye registros sin zona para migrar datos existentes."""
        mkw_ids = [c['id'] for c in batch]
        existing = {
            p.mikrowisp_id: p
            for p in Partner.search([
                ('mikrowisp_id', 'in', mkw_ids),
                '|',
                ('mikrowisp_zona', '=', zona),
                ('mikrowisp_zona', '=', False),
            ])
        }
        to_create = []
        log_vals = []
        updated = 0
        for cliente in batch:
            vals = self._build_partner_vals(cliente, country_ve_id, zona, city)
            partner = existing.get(cliente['id'])
            if partner:
                estado_anterior = partner.mikrowisp_estado
                estado_nuevo = vals.get('mikrowisp_estado')
                if estado_anterior != estado_nuevo:
                    log_vals.append({
                        'partner_id': partner.id,
                        'zona': zona,
                        'estado_anterior': estado_anterior,
                        'estado_nuevo': estado_nuevo,
                        'tipo_movimiento': tipo_movimiento(estado_anterior, estado_nuevo),
                    })
                partner.write(vals)
                updated += 1
            else:
                to_create.append(vals)
        if to_create:
            created = Partner.create(to_create)
            for partner, vals in zip(created, to_create):
                log_vals.append({
                    'partner_id': partner.id,
                    'zona': zona,
                    'estado_anterior': False,
                    'estado_nuevo': vals.get('mikrowisp_estado'),
                    'tipo_movimiento': tipo_movimiento(False, vals.get('mikrowisp_estado')),
                })
        if log_vals:
            self.env['mikrowisp.estado.log'].sudo().create(log_vals)
        return len(to_create), updated

    # -------------------------------------------------------------------------
    # Facturas (GetInvoices) — facturado y cobrado por cliente
    # -------------------------------------------------------------------------

    def _fetch_facturas_pagina(self, cfg, pagina):
        url = f"{cfg['url']}/api/v1/GetInvoices"
        payload = json.dumps({
            'token': cfg['token'],
            'limit': self._FACTURA_PAGE_SIZE,
            'pagina': pagina,
        }).encode()
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(
            url, data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(req, context=ctx, timeout=90) as r:
            data = json.loads(r.read())
        return data.get('facturas') or []

    def _build_factura_vals(self, factura, zona, partner_by_idcliente):
        def to_float(valor):
            try:
                return float(valor or 0)
            except (TypeError, ValueError):
                return 0.0

        def to_date(valor):
            return valor if valor and valor != '0000-00-00' else False

        idcliente = factura.get('idcliente') or 0
        return {
            'mikrowisp_factura_id': factura['id'],
            'zona': zona,
            'idcliente': idcliente,
            'partner_id': partner_by_idcliente.get(idcliente, False),
            'emitido': to_date(factura.get('emitido')),
            'vencimiento': to_date(factura.get('vencimiento')),
            'estado_factura': factura.get('estado') or '',
            'total': to_float(factura.get('total')),
            'cobrado': to_float(factura.get('cobrado')),
            'tipo_factura': factura.get('tipo_factura') or '',
        }

    def _write_facturas_batch(self, Factura, facturas, zona):
        ids = [f['id'] for f in facturas]
        existing = {
            f.mikrowisp_factura_id: f
            for f in Factura.search([('zona', '=', zona), ('mikrowisp_factura_id', 'in', ids)])
        }
        idclientes = list({f.get('idcliente') for f in facturas if f.get('idcliente')})
        partner_by_idcliente = {
            p.mikrowisp_id: p.id
            for p in self.env['res.partner'].sudo().search([
                ('mikrowisp_id', 'in', idclientes),
                ('mikrowisp_zona', '=', zona),
            ])
        }
        to_create = []
        updated = 0
        for factura in facturas:
            vals = self._build_factura_vals(factura, zona, partner_by_idcliente)
            rec = existing.get(factura['id'])
            if rec:
                rec.write(vals)
                updated += 1
            else:
                to_create.append(vals)
        if to_create:
            Factura.create(to_create)
        return len(to_create), updated

    def _sync_facturas(self, cfg, zona):
        if not cfg['url'] or not cfg['token']:
            _logger.warning('Mikrowisp [%s]: URL o token no configurados, omitiendo facturas.', zona)
            return 0, 0

        Factura = self.env['mikrowisp.factura'].sudo()
        ultima = Factura.search([('zona', '=', zona)], order='mikrowisp_factura_id desc', limit=1)
        ultimo_id_conocido = ultima.mikrowisp_factura_id if ultima else 0

        pagina = 1
        ya_conocidas = False
        paginas_extra = 0
        created = updated = 0

        try:
            while pagina <= self._FACTURA_MAX_PAGINAS:
                facturas = self._fetch_facturas_pagina(cfg, pagina)
                if not facturas:
                    # Página vacía: se llegó al final real de las facturas disponibles.
                    break

                c, u = self._write_facturas_batch(Factura, facturas, zona)
                created += c
                updated += u
                # Commit por página: una sincronización inicial puede tardar horas:
                # si se interrumpe, no se pierde el avance ya guardado.
                self.env.cr.commit()
                _logger.info(
                    'Mikrowisp [%s] facturas página=%s → %d creadas / %d actualizadas (acumulado)',
                    zona, pagina, created, updated,
                )

                if not ya_conocidas and min(f['id'] for f in facturas) <= ultimo_id_conocido:
                    ya_conocidas = True
                if ya_conocidas:
                    paginas_extra += 1
                    if paginas_extra >= self._FACTURA_REFRESH_EXTRA_PAGES:
                        break

                pagina += 1
        except Exception as exc:
            _logger.warning('Mikrowisp [%s]: error sincronizando facturas (página=%s) → %s', zona, pagina, exc)

        _logger.info('Mikrowisp [%s] facturas: sync completa → %d creadas / %d actualizadas', zona, created, updated)
        return created, updated

    # -------------------------------------------------------------------------
    # Sincronización por estado y por zona
    # -------------------------------------------------------------------------

    def _sync_estado_paginado(self, cfg, estado, estado_num, country_ve_id, zona, city):
        Partner = self.env['res.partner'].sudo()
        batch = []
        created = updated = 0
        try:
            for cliente in self._stream_clientes_paginado(cfg, estado_num):
                batch.append(cliente)
                if len(batch) >= self._BATCH_SIZE:
                    c, u = self._write_batch(Partner, batch, country_ve_id, zona, city)
                    created += c
                    updated += u
                    batch = []
                    _logger.info('Mikrowisp [%s/%s]: %d creados / %d actualizados (paginado, parcial)', zona, estado, created, updated)
        except Exception as exc:
            _logger.warning('Mikrowisp [%s]: error paginado estado=%s → %s', zona, estado, exc)
        if batch:
            c, u = self._write_batch(Partner, batch, country_ve_id, zona, city)
            created += c
            updated += u
        _logger.info('Mikrowisp [%s] estado=%s (paginado) → %d creados / %d actualizados', zona, estado, created, updated)
        return created + updated

    def _sync_estado(self, cfg, estado, country_ve_id, zona, city):
        if estado in _ESTADOS_PAGINADOS:
            return self._sync_estado_paginado(cfg, estado, _ESTADOS_PAGINADOS[estado], country_ve_id, zona, city)

        Partner = self.env['res.partner'].sudo()
        batch = []
        created = updated = 0

        try:
            for cliente in self._stream_clientes(cfg, estado):
                batch.append(cliente)
                if len(batch) >= self._BATCH_SIZE:
                    c, u = self._write_batch(Partner, batch, country_ve_id, zona, city)
                    created += c
                    updated += u
                    batch = []
                    _logger.info('Mikrowisp [%s/%s]: %d creados / %d actualizados (parcial)', zona, estado, created, updated)
        except Exception as exc:
            _logger.warning('Mikrowisp [%s]: error streaming estado=%s → %s', zona, estado, exc)

        if batch:
            c, u = self._write_batch(Partner, batch, country_ve_id, zona, city)
            created += c
            updated += u

        _logger.info('Mikrowisp [%s] estado=%s → %d creados / %d actualizados', zona, estado, created, updated)
        return created + updated

    def _sync_zone(self, url, token, zona, city):
        if not url or not token:
            _logger.warning('Mikrowisp [%s]: URL o token no configurados, omitiendo.', zona)
            return 0

        cfg = {'url': url.rstrip('/'), 'token': token}
        country_ve = self.env.ref('base.ve', raise_if_not_found=False)
        country_ve_id = country_ve.id if country_ve else False

        total = 0
        for estado in _ESTADOS:
            total += self._sync_estado(cfg, estado, country_ve_id, zona, city)

        _logger.info('Mikrowisp [%s]: sync completa → %d clientes procesados', zona, total)
        return total

    # -------------------------------------------------------------------------
    # Punto de entrada global (cron único para todas las zonas)
    # -------------------------------------------------------------------------

    @api.model
    def cron_sync_clients(self):
        """Sincroniza todas las zonas (cada zona también tiene su propio cron independiente)."""
        for zona in self._ZONAS:
            self.env[f'mikrowisp.sync.{zona}'].cron_sync_clients()

    @api.model
    def action_sync_now(self):
        self.cron_sync_clients()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Mikrowisp',
                'message': 'Sincronización de todas las zonas completada.',
                'type': 'success',
                'sticky': False,
            },
        }

    @api.model
    def cron_sync_facturas(self):
        """Sincroniza facturas de todas las zonas. La primera corrida trae todo el histórico."""
        for zona in self._ZONAS:
            self.env[f'mikrowisp.sync.{zona}'].cron_sync_facturas()

    @api.model
    def action_sync_facturas_now(self):
        self.cron_sync_facturas()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Mikrowisp',
                'message': 'Sincronización de facturas de todas las zonas completada.',
                'type': 'success',
                'sticky': False,
            },
        }
