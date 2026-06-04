{
    "name": "Venezuela - Datos Adicionales (Territorial, RIF, Bancos)",
    "summary": "Complementa l10n_ve con división político-territorial, "
               "tipos de identificación SENIAT (RIF), tipos de responsabilidad "
               "fiscal y bancos venezolanos.",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "author": "Nisbe (port a Odoo 19) — basado en SINAPSYS GLOBAL / MASTERCORE SAS",
    "countries": ["ve"],
    "depends": [
        "base",
        "contacts",
        "account",
        "l10n_ve",
        "l10n_latam_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/l10n_latam_identification_type_data.xml",
        "data/l10n_ve_responsibility_type_data.xml",
        "data/res.country.state.csv",
        "data/res.country.state.municipality.csv",
        "data/res.country.state.municipality.parish.csv",
        "data/res_bank.xml",
        "views/l10n_ve_responsibility_type_view.xml",
        "views/res_country_state_municipality_view.xml",
        "views/res_partner_view.xml",
    ],
    "installable": True,
    "application": False,
}
