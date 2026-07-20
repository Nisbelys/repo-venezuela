from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Zona Caracas
    mikrowisp_url = fields.Char(
        string='URL Mikrowisp Caracas',
        config_parameter='mikrowisp.url',
    )
    mikrowisp_token = fields.Char(
        string='Token API Caracas',
        config_parameter='mikrowisp.token',
    )

    # Zona Los Llanos
    mikrowisp_llanos_url = fields.Char(
        string='URL Mikrowisp Los Llanos',
        config_parameter='mikrowisp.llanos.url',
    )
    mikrowisp_llanos_token = fields.Char(
        string='Token API Los Llanos',
        config_parameter='mikrowisp.llanos.token',
    )

    # Zona Puente Hierro
    mikrowisp_puentehierro_url = fields.Char(
        string='URL Mikrowisp Puente Hierro',
        config_parameter='mikrowisp.puentehierro.url',
    )
    mikrowisp_puentehierro_token = fields.Char(
        string='Token API Puente Hierro',
        config_parameter='mikrowisp.puentehierro.token',
    )

    # Zona Ocumare
    mikrowisp_ocumare_url = fields.Char(
        string='URL Mikrowisp Ocumare',
        config_parameter='mikrowisp.ocumare.url',
    )
    mikrowisp_ocumare_token = fields.Char(
        string='Token API Ocumare',
        config_parameter='mikrowisp.ocumare.token',
    )

    def action_mikrowisp_sync_now(self):
        return self.env['mikrowisp.sync'].action_sync_now()

    def action_mikrowisp_sync_caracas(self):
        return self.env['mikrowisp.sync.caracas'].action_sync_now()

    def action_mikrowisp_sync_llanos(self):
        return self.env['mikrowisp.sync.llanos'].action_sync_now()

    def action_mikrowisp_sync_puentehierro(self):
        return self.env['mikrowisp.sync.puentehierro'].action_sync_now()

    def action_mikrowisp_sync_ocumare(self):
        return self.env['mikrowisp.sync.ocumare'].action_sync_now()

    def action_mikrowisp_sync_facturas_caracas(self):
        return self.env['mikrowisp.sync.caracas'].action_sync_facturas_now()

    def action_mikrowisp_sync_facturas_llanos(self):
        return self.env['mikrowisp.sync.llanos'].action_sync_facturas_now()

    def action_mikrowisp_sync_facturas_puentehierro(self):
        return self.env['mikrowisp.sync.puentehierro'].action_sync_facturas_now()

    def action_mikrowisp_sync_facturas_ocumare(self):
        return self.env['mikrowisp.sync.ocumare'].action_sync_facturas_now()
