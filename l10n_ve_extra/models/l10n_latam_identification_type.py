from odoo import fields, models


class L10nLatamIdentificationType(models.Model):
    _inherit = "l10n_latam.identification.type"

    l10n_ve_code = fields.Char(
        string="Código SENIAT",
        help="Prefijo SENIAT del tipo de identificación (V, E, J, G, P, C).",
    )
