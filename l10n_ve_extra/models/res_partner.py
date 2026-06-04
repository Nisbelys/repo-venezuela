from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    municipality_id = fields.Many2one(
        "res.country.state.municipality",
        string="Municipio",
        domain="[('state_id', '=', state_id)]",
        ondelete="restrict",
    )
    parish_id = fields.Many2one(
        "res.country.state.municipality.parish",
        string="Parroquia",
        domain="[('municipality_id', '=', municipality_id)]",
        ondelete="restrict",
    )
    l10n_ve_responsibility_type_id = fields.Many2one(
        "l10n_ve.responsibility.type",
        string="Tipo de Responsabilidad SENIAT",
        index=True,
    )
