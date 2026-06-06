from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mikrowisp_url = fields.Char(
        string='URL de Mikrowisp',
        config_parameter='mikrowisp.url',
        placeholder='https://tu-servidor.com',
    )
    mikrowisp_token = fields.Char(
        string='Token API',
        config_parameter='mikrowisp.token',
    )

    def action_mikrowisp_sync_now(self):
        return self.env['mikrowisp.sync'].action_sync_now()
