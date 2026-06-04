from odoo import fields, models


class L10nVeResponsibilityType(models.Model):
    _name = "l10n_ve.responsibility.type"
    _description = "SENIAT Responsibility Type"
    _order = "sequence, code"

    name = fields.Char(required=True, index=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Name must be unique."),
        ("code_uniq", "unique(code)", "Code must be unique."),
    ]
