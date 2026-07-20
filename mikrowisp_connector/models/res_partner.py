from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_mikrowisp = fields.Boolean(
        string='Es cliente Mikrowisp',
        default=False,
        index=True,
    )
    mikrowisp_zona = fields.Char(
        string='Zona',
        index=True,
        readonly=True,
    )
    mikrowisp_id = fields.Integer(
        string='ID Mikrowisp',
        index=True,
        copy=False,
        readonly=True,
    )
    mikrowisp_codigo = fields.Char(string='Código', readonly=True)
    mikrowisp_cedula = fields.Char(string='Cédula', readonly=True)
    mikrowisp_estado = fields.Selection(
        selection=[
            ('ACTIVO', 'Activo'),
            ('SUSPENDIDO', 'Suspendido'),
            ('CORTADO', 'Cortado'),
            ('RETIRADO', 'Retirado'),
        ],
        string='Estado',
        index=True,
        readonly=True,
    )
    mikrowisp_service_status = fields.Selection(
        selection=[
            ('ONLINE', 'En línea'),
            ('OFFLINE', 'Fuera de línea'),
        ],
        string='Conexión PPP',
        index=True,
        readonly=True,
    )
    mikrowisp_ip = fields.Char(string='IP asignada', readonly=True)
    mikrowisp_mac = fields.Char(string='MAC', readonly=True)
    mikrowisp_plan = fields.Char(string='Plan', readonly=True)
    mikrowisp_deuda = fields.Float(
        string='Deuda ($)',
        digits=(10, 2),
        readonly=True,
    )
    mikrowisp_facturas_nopagadas = fields.Integer(
        string='Facturas pendientes',
        readonly=True,
    )
    mikrowisp_last_sync = fields.Datetime(
        string='Última sincronización',
        readonly=True,
    )
