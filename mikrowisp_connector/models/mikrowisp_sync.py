import json
import logging
import ssl
import urllib.request

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

_ESTADOS = ['ACTIVO', 'SUSPENDIDO', 'CORTADO', 'RETIRADO']
_VALID_ESTADOS = set(_ESTADOS)
_VALID_SERVICE_STATUS = {'ONLINE', 'OFFLINE'}


class MikrowispSync(models.AbstractModel):
    _name = 'mikrowisp.sync'
    _description = 'Servicio de sincronización Mikrowisp (solo lectura)'

    # -------------------------------------------------------------------------
    # Helpers de API
    # -------------------------------------------------------------------------

    def _get_config(self):
        get = self.env['ir.config_parameter'].sudo().get_param
        return {
            'url': get('mikrowisp.url', '').rstrip('/'),
            'token': get('mikrowisp.token', ''),
        }

    def _api_post(self, endpoint, payload, timeout=120):
        cfg = self._get_config()
        if not cfg['url'] or not cfg['token']:
            raise ValueError('Mikrowisp: configure la URL y el Token API en Ajustes.')
        payload['token'] = cfg['token']
        url = f"{cfg['url']}/api/v1/{endpoint}"
        data = json.dumps(payload).encode()
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(
            url, data=data,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8', errors='ignore'))

    # -------------------------------------------------------------------------
    # Construcción de valores para res.partner
    # -------------------------------------------------------------------------

    def _build_partner_vals(self, cliente, country_ve_id):
        servicios = cliente.get('servicios') or []
        svc = servicios[0] if servicios else {}
        facturacion = cliente.get('facturacion') or {}

        estado = (cliente.get('estado') or '').upper()
        svc_status = (svc.get('status_user') or '').upper()

        return {
            'name': cliente.get('nombre') or 'Sin nombre',
            'email': cliente.get('correo') or False,
            'phone': cliente.get('telefono') or False,
            'mobile': cliente.get('movil') or False,
            'street': cliente.get('direccion_principal') or False,
            'city': 'Caracas',
            'country_id': country_ve_id,
            'customer_rank': 1,
            'is_mikrowisp': True,
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
    # Sincronización por estado
    # -------------------------------------------------------------------------

    def _sync_estado(self, estado, country_ve_id):
        try:
            result = self._api_post('GetClientsDetails', {'estado': estado})
        except Exception as exc:
            _logger.warning('Mikrowisp: error al consultar estado=%s → %s', estado, exc)
            return 0

        if result.get('estado') != 'exito':
            _logger.warning(
                'Mikrowisp: respuesta no exitosa para estado=%s → %s',
                estado, result.get('mensaje', ''),
            )
            return 0

        clientes = result.get('datos') or []
        if not clientes:
            return 0

        Partner = self.env['res.partner'].sudo()

        mkw_ids = [c['id'] for c in clientes if c.get('id')]
        existing = {
            p.mikrowisp_id: p
            for p in Partner.search([('mikrowisp_id', 'in', mkw_ids)])
        }

        to_create = []
        for cliente in clientes:
            mkw_id = cliente.get('id')
            if not mkw_id:
                continue
            vals = self._build_partner_vals(cliente, country_ve_id)
            partner = existing.get(mkw_id)
            if partner:
                partner.write(vals)
            else:
                to_create.append(vals)

        if to_create:
            Partner.create(to_create)

        _logger.info(
            'Mikrowisp sync estado=%s → %d creados / %d actualizados',
            estado, len(to_create), len(existing),
        )
        return len(clientes)

    # -------------------------------------------------------------------------
    # Puntos de entrada públicos
    # -------------------------------------------------------------------------

    @api.model
    def cron_sync_clients(self):
        country_ve = self.env.ref('base.ve', raise_if_not_found=False)
        country_ve_id = country_ve.id if country_ve else False
        total = 0
        for estado in _ESTADOS:
            total += self._sync_estado(estado, country_ve_id)
        _logger.info('Mikrowisp: sincronización completa → %d clientes procesados', total)

    @api.model
    def action_sync_now(self):
        self.cron_sync_clients()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Mikrowisp',
                'message': 'Sincronización completada con éxito.',
                'type': 'success',
                'sticky': False,
            },
        }
