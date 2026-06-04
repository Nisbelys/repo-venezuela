# Odoo Enterprise License System — Technical Documentation

> **Disclaimer:** This document is for educational/analysis purposes only.

---

## Overview

Odoo Enterprise uses a license validation system that:
1. Sends a weekly "ping" to `services.odoo.com` with database info.
2. Stores the license state in `ir.config_parameter` (database).
3. Displays warnings in the UI based on expiration status.
4. Blocks the UI entirely when the license expires.

---

## Enterprise Modules Location

Enterprise and community modules have been **separated into two directories**:

```
odoo/
├── addons/               ← Community/Core modules (681 modules, LGPL-3)
└── addons-enterprise/    ← Enterprise modules (736 modules, OEEL-1)
```

Originally, Odoo ships both in a single `odoo/addons/` directory. They were separated by
reading the `'license'` field in each module's `__manifest__.py`:
- `'license': 'OEEL-1'` → moved to `odoo/addons-enterprise/`
- `'license': 'LGPL-3'` or `'AGPL-3'` → stays in `odoo/addons/`

---

## Setup Process

### 1. Configure `addons_path`

Odoo needs to know about both directories. When starting Odoo, pass both paths via the
`--addons-path` argument or in your `odoo.conf`:

**Option A — Command line:**

```bash
./odoo-bin --addons-path=odoo/addons,odoo/addons-enterprise
```

**Option B — Configuration file (`odoo.conf`):**

```ini
[options]
addons_path = odoo/addons,odoo/addons-enterprise
```

### 2. Apply the database-level changes (Point #5 — per database)

After creating or accessing your database, run via **Odoo shell** (`./odoo-bin shell -d <dbname>`):

```python
self.env['ir.config_parameter'].sudo().set_param('database.expiration_date', '2099-12-31 23:59:59')
self.env['ir.config_parameter'].sudo().set_param('database.expiration_reason', 'renewal')
self.env.cr.commit()
```

Or via **SQL** (PostgreSQL):

```sql
INSERT INTO ir_config_parameter (key, value, create_uid, create_date, write_uid, write_date)
VALUES ('database.expiration_date', '2099-12-31 23:59:59', 1, NOW(), 1, NOW())
ON CONFLICT (key) DO UPDATE SET value = '2099-12-31 23:59:59', write_date = NOW();

INSERT INTO ir_config_parameter (key, value, create_uid, create_date, write_uid, write_date)
VALUES ('database.expiration_reason', 'renewal', 1, NOW(), 1, NOW())
ON CONFLICT (key) DO UPDATE SET value = 'renewal', write_date = NOW();

DELETE FROM ir_config_parameter WHERE key IN (
    'database.already_linked_subscription_url',
    'database.already_linked_email',
    'database.already_linked_send_mail_url'
);
```

### 3. Deactivate the cron on existing databases

The XML change to deactivate the cron (Point #1) is inside a `noupdate="1"` block, so it
**only applies to new databases**. For existing databases, deactivate it manually:

**Via the UI:** Settings → Technical → Scheduled Actions → "Publisher: Update Notification" → uncheck Active

**Via SQL:**

```sql
UPDATE ir_cron SET active = false
WHERE id = (
    SELECT res_id FROM ir_model_data
    WHERE module = 'mail' AND name = 'ir_cron_module_update_notification'
);
```

> **Note:** Since Point #2 (the Python no-op) is already applied in the source code, the cron
> is harmless even if it runs — it does nothing. This step is optional but recommended for
> cleanliness.

### 4. Summary checklist

| Step | Where | When | Required? |
|---|---|---|---|
| Set `addons_path` to include both directories | `odoo.conf` or CLI | Before starting Odoo | Yes |
| Set `database.expiration_date` to far future | Database (shell/SQL) | Per database | Yes |
| Set `database.expiration_reason` to `renewal` | Database (shell/SQL) | Per database | Yes |
| Deactivate the cron | Database (UI/SQL) | Per existing database | Optional (safe due to #2) |

### Enterprise Modules (OEEL-1) — 736 modules

```
account_3way_match                          account_accountant
account_accountant_batch_payment            account_accountant_check_printing
account_accountant_fleet                    account_asset
account_asset_fleet                         account_avatax
account_avatax_geolocalize                  account_avatax_sale
account_avatax_stock                        account_bank_statement_extract
account_bank_statement_import               account_bank_statement_import_camt
account_bank_statement_import_csv           account_bank_statement_import_ofx
account_bank_statement_import_qif           account_base_import
account_batch_payment                       account_budget
account_budget_purchase                     account_external_tax
account_extract                             account_fiscal_categories
account_fiscal_categories_fleet             account_followup
account_inter_company_rules                 account_intrastat
account_invoice_extract                     account_invoice_extract_purchase
account_iso20022                            account_loans
account_online_synchronization              account_reports
account_reports_cash_basis                  account_saft
account_saft_import                         account_sepa_direct_debit
account_transfer                            account_winbooks_import
accountant                                  accountant_fleet
accountant_hr_expense                       accountant_knowledge
ai                                          ai_account
ai_app                                      ai_auto_install
ai_crm                                      ai_crm_livechat
ai_documents                                ai_documents_account
ai_documents_source                         ai_knowledge
ai_livechat                                 ai_website
ai_website_livechat                         analytic_enterprise
appointment                                 appointment_account_payment
appointment_crm                             appointment_google_calendar
appointment_google_reserve                  appointment_hr
appointment_hr_recruitment                  appointment_microsoft_calendar
appointment_sms                             approvals
approvals_purchase                          approvals_purchase_stock
base_automation_hr                          certificate
contacts_enterprise                         crm_enterprise
crm_enterprise_partner_assign               crm_helpdesk
crm_sale_subscription                       currency_rate_live
data_cleaning                               data_merge_crm
data_merge_helpdesk                         data_merge_project
data_merge_stock_account                    data_merge_utm
databases                                   delivery_bpost
delivery_dhl                                delivery_dhl_rest
delivery_easypost                           delivery_envia
delivery_fedex                              delivery_fedex_rest
delivery_iot                                delivery_sendcloud
delivery_shiprocket                         delivery_starshipit
delivery_ups                                delivery_ups_rest
delivery_usps                               delivery_usps_rest
digest_enterprise                           documents
documents_account                           documents_account_peppol
documents_approvals                         documents_fleet
documents_fsm                               documents_hr
documents_hr_expense                        documents_hr_holidays
documents_hr_payroll                        documents_l10n_be_hr_payroll
documents_l10n_ch_hr_payroll                documents_l10n_hk_hr_payroll
documents_l10n_ke_hr_payroll                documents_l10n_mx_hr_payroll_account_edi
documents_product                           documents_project
documents_project_sale                      documents_project_sign
documents_sign                              documents_spreadsheet
documents_spreadsheet_survey                esg
esg_csrd                                    esg_csrd_ai
esg_csrd_hr                                 esg_csrd_hr_fleet
esg_hr                                      esg_hr_fleet
esg_project                                 event_enterprise
event_iot                                   event_sale_iot
event_social                                frontdesk
helpdesk                                    helpdesk_account
helpdesk_fsm                                helpdesk_fsm_report
helpdesk_fsm_sale                           helpdesk_holidays
helpdesk_mail_plugin                        helpdesk_repair
helpdesk_sale                               helpdesk_sale_loyalty
helpdesk_sale_timesheet                     helpdesk_sms
helpdesk_stock                              helpdesk_stock_account
helpdesk_timesheet                          hr_appraisal
hr_appraisal_skills                         hr_appraisal_survey
hr_attendance_gantt                         hr_contract_salary
hr_contract_salary_holidays                 hr_contract_salary_payroll
hr_expense_extract                          hr_expense_predict_product
hr_gantt                                    hr_holidays_gantt
hr_mobile                                   hr_payroll
hr_payroll_account                          hr_payroll_account_iso20022
hr_payroll_attendance                       hr_payroll_expense
hr_payroll_fleet                            hr_payroll_holidays
hr_payroll_planning                         hr_payroll_sale_commission
hr_recruitment_ai                           hr_recruitment_extract
hr_recruitment_integration_base             hr_recruitment_integration_monster
hr_recruitment_integration_skills_monster   hr_recruitment_integration_website
hr_recruitment_integration_website_monster  hr_recruitment_reports
hr_recruitment_sign                         hr_referral
hr_sign                                     hr_work_entry_attendance
hr_work_entry_enterprise                    hr_work_entry_holidays_enterprise
hr_work_entry_planning                      hr_work_entry_planning_attendance
iap_extract                                 industry_fsm
industry_fsm_repair                         industry_fsm_report
industry_fsm_sale                           industry_fsm_sale_report
industry_fsm_sale_subscription              industry_fsm_sms
industry_fsm_stock                          iot
knowledge                                   l10n_ae_faf
l10n_ae_hr_payroll                          l10n_ae_hr_payroll_account
l10n_ae_reports                             l10n_ar_edi
l10n_ar_reports                             l10n_ar_reports_simple
l10n_at_intrastat                           l10n_at_pos
l10n_at_reports                             l10n_at_saft
l10n_au_aba                                 l10n_au_hr_payroll
l10n_au_hr_payroll_account                  l10n_au_hr_payroll_api
l10n_au_reports                             l10n_bd_hr_payroll
l10n_bd_hr_payroll_account                  l10n_bd_reports
l10n_be_coda                                l10n_be_codabox
l10n_be_codaclean                           l10n_be_fiscal_categories
l10n_be_fiscal_categories_fleet             l10n_be_hr_contract_salary
l10n_be_hr_payroll                          l10n_be_hr_payroll_account
l10n_be_hr_payroll_acerta                   l10n_be_hr_payroll_attendance
l10n_be_hr_payroll_dimona                   l10n_be_hr_payroll_dimona_auto
l10n_be_hr_payroll_fix                      l10n_be_hr_payroll_fleet
l10n_be_hr_payroll_group_s                  l10n_be_hr_payroll_partena
l10n_be_hr_payroll_prisma                   l10n_be_hr_payroll_sd_worx
l10n_be_hr_payroll_ucm                      l10n_be_intervat
l10n_be_intrastat                           l10n_be_reports
l10n_be_reports_client_nihil                l10n_be_reports_hr_payroll
l10n_be_reports_sms                         l10n_be_soda
l10n_bf_reports                             l10n_bg_reports
l10n_bg_reports_ledger                      l10n_bh_reports
l10n_bj_reports                             l10n_bo_reports
l10n_br_avatax                              l10n_br_avatax_sale
l10n_br_edi                                 l10n_br_edi_fiscal_reform
l10n_br_edi_pos                             l10n_br_edi_pos_fiscal_reform
l10n_br_edi_sale                            l10n_br_edi_sale_fiscal_reform
l10n_br_edi_stock                           l10n_br_edi_website_sale
l10n_br_reports                             l10n_br_sale_subscription
l10n_br_website_sale_fiscal_reform          l10n_ca_check_printing
l10n_ca_payment_cpa005                      l10n_ca_reports
l10n_cd_reports                             l10n_cf_reports
l10n_cg_reports                             l10n_ch_hr_payroll
l10n_ch_hr_payroll_account                  l10n_ch_hr_payroll_elm_transmission_5_3
l10n_ch_reports                             l10n_ci_reports
l10n_cl_edi                                 l10n_cl_edi_exports
l10n_cl_edi_factoring                       l10n_cl_edi_pos
l10n_cl_edi_stock                           l10n_cl_edi_website_sale
l10n_cl_reports                             l10n_cm_reports
l10n_cn_reports                             l10n_co_dian
l10n_co_edi                                 l10n_co_edi_mandate
l10n_co_reports                             l10n_cy_reports
l10n_cz_intrastat                           l10n_cz_reports
l10n_de_intrastat                           l10n_de_pos_cert
l10n_de_pos_res_cert                        l10n_de_reports
l10n_din5008_account_followup               l10n_din5008_industry_fsm
l10n_din5008_sale_renting                   l10n_dk_intrastat
l10n_dk_reports                             l10n_dk_saft_import
l10n_do_check_printing                      l10n_do_reports
l10n_dz_reports                             l10n_ec_edi_pos
l10n_ee_intrastat                           l10n_ee_reports
l10n_eg_hr_payroll                          l10n_eg_hr_payroll_account
l10n_eg_reports                             l10n_employment_hero
l10n_es_intrastat                           l10n_es_real_estates
l10n_es_reports                             l10n_es_reports_2024
l10n_es_reports_2025                        l10n_es_sale_amazon
l10n_et_reports                             l10n_eu_iot_scale_cert
l10n_eu_oss_reports                         l10n_fi_intrastat
l10n_fi_reports                             l10n_fr_fec_import
l10n_fr_hr_payroll                          l10n_fr_hr_payroll_account
l10n_fr_intrastat                           l10n_fr_reports
l10n_ga_reports                             l10n_gn_reports
l10n_gq_reports                             l10n_gr_reports
l10n_gt_edi_pos                             l10n_gw_reports
l10n_hk_hr_payroll                          l10n_hk_hr_payroll_account
l10n_hk_hr_payroll_empf                     l10n_hk_reports
l10n_hr_edi                                 l10n_hr_intrastat
l10n_hr_kuna_reports                        l10n_hr_reports
l10n_hu_reports                             l10n_id_hr_payroll
l10n_id_hr_payroll_account                  l10n_ie_intrastat
l10n_ie_reports                             l10n_il_reports
l10n_in_asset                               l10n_in_edi_gstr
l10n_in_hr_payroll                          l10n_in_hr_payroll_account
l10n_in_pos_urban_piper                     l10n_in_reports
l10n_in_reports_gstr_pos                    l10n_it_hr_payroll_sd_worx
l10n_it_intrastat                           l10n_it_pos
l10n_it_reports                             l10n_jo_edi_pos
l10n_jo_hr_payroll                          l10n_jo_hr_payroll_account
l10n_jo_reports                             l10n_jp_reports
l10n_jp_zengin                              l10n_ke_edi_oscu
l10n_ke_edi_oscu_mrp                        l10n_ke_edi_oscu_pos
l10n_ke_edi_oscu_stock                      l10n_ke_hr_payroll
l10n_ke_hr_payroll_account                  l10n_ke_reports
l10n_kh_reports                             l10n_km_reports
l10n_kr_reports                             l10n_kz_reports
l10n_lk_reports                             l10n_lt_hr_payroll
l10n_lt_hr_payroll_account                  l10n_lt_intrastat
l10n_lt_reports                             l10n_lt_saft
l10n_lt_saft_import                         l10n_lu_hr_payroll
l10n_lu_hr_payroll_account                  l10n_lu_reports
l10n_lv_reports                             l10n_ma_hr_payroll
l10n_ma_hr_payroll_account                  l10n_ma_reports
l10n_ml_reports                             l10n_mn_reports
l10n_mr_reports                             l10n_mt_reports
l10n_mu_reports                             l10n_mx_edi
l10n_mx_edi_extended                        l10n_mx_edi_landing
l10n_mx_edi_pos                             l10n_mx_edi_sale
l10n_mx_edi_stock                           l10n_mx_edi_website_sale
l10n_mx_hr_payroll                          l10n_mx_hr_payroll_account
l10n_mx_hr_payroll_account_edi              l10n_mx_reports
l10n_mx_reports_closing                     l10n_mx_xml_polizas
l10n_my_hr_payroll                          l10n_my_hr_payroll_account
l10n_my_reports                             l10n_mz_reports
l10n_ne_reports                             l10n_ng_reports
l10n_nl_hr_payroll                          l10n_nl_hr_payroll_account
l10n_nl_intrastat                           l10n_nl_reports
l10n_no_reports                             l10n_no_saft
l10n_nz_eft                                 l10n_nz_reports
l10n_om_reports                             l10n_pe_edi
l10n_pe_edi_pos                             l10n_pe_edi_stock
l10n_pe_reports                             l10n_pe_reports_lib
l10n_pe_reports_stock                       l10n_ph_check_printing
l10n_ph_reports                             l10n_pk_hr_payroll
l10n_pk_hr_payroll_account                  l10n_pk_reports
l10n_pl_hr_payroll                          l10n_pl_hr_payroll_account
l10n_pl_intrastat                           l10n_pl_reports
l10n_pl_reports_account_saft                l10n_pl_reports_pos_jpk
l10n_pt_intrastat                           l10n_pt_reports
l10n_ro_hr_payroll                          l10n_ro_hr_payroll_account
l10n_ro_intrastat                           l10n_ro_reports
l10n_ro_saft                                l10n_ro_saft_import
l10n_rs_reports                             l10n_rw_reports
l10n_sa_hr_payroll                          l10n_sa_hr_payroll_account
l10n_sa_reports                             l10n_se_bban
l10n_se_pos                                 l10n_se_reports
l10n_se_returns                             l10n_se_sie4_export
l10n_se_sie4_import                         l10n_se_sie_import
l10n_sg_reports                             l10n_si_intrastat
l10n_si_reports                             l10n_sk_hr_payroll
l10n_sk_hr_payroll_account                  l10n_sk_reports
l10n_sn_reports                             l10n_syscohada_reports
l10n_td_reports                             l10n_tg_reports
l10n_th_reports                             l10n_tn_reports
l10n_tr_hr_payroll                          l10n_tr_hr_payroll_account
l10n_tr_reports                             l10n_tw_reports
l10n_tz_reports                             l10n_ug_reports
l10n_uk_bacs                                l10n_uk_hmrc
l10n_uk_intrastat                           l10n_uk_reports
l10n_uk_reports_cis                         l10n_us_1099
l10n_us_check_printing                      l10n_us_direct_deposit
l10n_us_hr_payroll                          l10n_us_hr_payroll_account
l10n_us_hr_payroll_adp                      l10n_us_payment_nacha
l10n_us_reports                             l10n_uy_edi
l10n_uy_edi_stock                           l10n_uy_reports
l10n_vn_reports                             l10n_za_reports
l10n_zm_reports                             mail_enterprise
mail_mobile                                 maintenance_worksheet
marketing_automation                        marketing_automation_crm
marketing_automation_sms                    marketing_automation_website_sale
marketing_automation_whatsapp               mass_mailing_sale_subscription
mrp_account_enterprise                      mrp_accountant
mrp_maintenance                             mrp_mps
mrp_plm                                     mrp_subcontracting_account_enterprise
mrp_subcontracting_enterprise               mrp_subcontracting_quality
mrp_workorder                               mrp_workorder_expiry
mrp_workorder_hr_account                    mrp_workorder_iot
mrp_workorder_plm                           partner_commission
payment_sepa_direct_debit                   planning
planning_attendance                         planning_holidays
planning_hr_skills                          pos_account_reports
pos_appointment                             pos_avatax
pos_barcodelookup                           pos_blackbox_be
pos_enterprise                              pos_enterprise_sms_whatsapp
pos_event_iot                               pos_hr_mobile
pos_iot                                     pos_iot_adam_scale
pos_iot_ingenico                            pos_iot_six
pos_iot_worldline                           pos_mobile
pos_online_payment_self_order_preparation_display
pos_order_tracking_display                  pos_pricer
pos_restaurant_appointment                  pos_restaurant_preparation_display
pos_restaurant_urban_piper                  pos_sale_stock_renting
pos_sale_subscription                       pos_self_order_iot
pos_self_order_preparation_display          pos_settle_due
pos_tyro                                    pos_urban_piper
pos_urban_piper_enhancements                pos_urban_piper_ubereats
product_barcodelookup                       product_unspsc
project_account_asset                       project_account_budget
project_enterprise                          project_enterprise_hr
project_enterprise_hr_skills                project_forecast
project_helpdesk                            project_holidays
project_hr_payroll_account                  project_hr_skills
project_sale_subscription                   project_timesheet_forecast
project_timesheet_forecast_sale             purchase_accountant
purchase_intrastat                          purchase_mrp_workorder_quality
quality                                     quality_control
quality_control_iot                         quality_control_picking_batch
quality_control_worksheet                   quality_iot
quality_mrp                                 quality_mrp_workorder
quality_mrp_workorder_iot                   quality_mrp_workorder_worksheet
quality_repair                              room
sale_account_accountant                     sale_amazon
sale_amazon_avatax                          sale_commission
sale_commission_margin                      sale_commission_subscription
sale_enterprise                             sale_external_tax
sale_intrastat                              sale_lazada
sale_management_renting                     sale_mrp_renting
sale_planning                               sale_project_forecast
sale_purchase_inter_company_rules           sale_purchase_stock_inter_company_rules
sale_renting                                sale_renting_crm
sale_renting_planning                       sale_shopee
sale_stock_renting                          sale_subscription
sale_subscription_external_tax              sale_subscription_partnership
sale_subscription_stock                     sale_subscription_timesheet
sale_timesheet_enterprise                   sale_timesheet_enterprise_holidays
sign                                        sign_ai
sign_emsigner                               sign_itsme
snailmail_account_followup                  social
social_crm                                  social_demo
social_facebook                             social_instagram
social_linkedin                             social_push_notifications
social_sale                                 social_test_full
social_twitter                              social_youtube
spreadsheet_dashboard_account_accountant    spreadsheet_dashboard_crm
spreadsheet_dashboard_documents             spreadsheet_dashboard_edition
spreadsheet_dashboard_helpdesk              spreadsheet_dashboard_hr_payroll
spreadsheet_dashboard_hr_referral           spreadsheet_dashboard_mrp_account
spreadsheet_dashboard_purchase_stock        spreadsheet_dashboard_sale_renting
spreadsheet_dashboard_sale_subscription     spreadsheet_dashboard_stock
spreadsheet_edition                         spreadsheet_sale_management
stock_accountant                            stock_barcode
stock_barcode_barcodelookup                 stock_barcode_mrp
stock_barcode_mrp_subcontracting            stock_barcode_picking_batch
stock_barcode_product_expiry                stock_barcode_quality_control
stock_barcode_quality_control_picking_batch stock_barcode_quality_mrp
stock_enterprise                            stock_fleet_enterprise
stock_intrastat                             test_appointment_full
test_data_cleaning                          test_discuss_full_enterprise
test_documents_full                         test_l10n_be_hr_payroll_account
test_l10n_hk_hr_payroll_account             test_l10n_us_hr_payroll_account
test_mail_enterprise                        test_marketing_automation
test_sale_subscription                      test_sign
test_spreadsheet_edition                    test_timer
test_web_cohort                             test_web_gantt
test_web_studio                             test_website_sale_full
timer                                       timesheet_grid
timesheet_grid_holidays                     voip
voip_ai                                     voip_crm
voip_helpdesk                               voip_hr
voip_hr_recruitment                         voip_onsip
voip_sale_subscription                      voip_sms
web_cohort                                  web_enterprise
web_gantt                                   web_grid
web_map                                     web_mobile
web_studio                                  website_appointment
website_appointment_account_payment         website_appointment_crm
website_appointment_sale                    website_appointment_sale_project
website_crm_iap_reveal_enterprise           website_delivery_sendcloud
website_documents                           website_enterprise
website_event_social                        website_event_track_gantt
website_event_track_social                  website_generator
website_generator_sale                      website_helpdesk
website_helpdesk_forum                      website_helpdesk_knowledge
website_helpdesk_livechat                   website_helpdesk_sale_loyalty
website_helpdesk_slides                     website_helpdesk_slides_forum
website_knowledge                           website_product_barcodelookup
website_sale_dashboard                      website_sale_external_tax
website_sale_fedex                          website_sale_renting
website_sale_renting_planning               website_sale_stock_renting
website_sale_subscription                   website_sale_ups
website_studio                              whatsapp
whatsapp_account                            whatsapp_account_followup
whatsapp_calendar                           whatsapp_delivery
whatsapp_event                              whatsapp_hr_referral
whatsapp_payment                            whatsapp_pos
whatsapp_sale                               whatsapp_sign
whatsapp_stock                              whatsapp_website_sale
worksheet
```

### Community/Core Modules (LGPL-3) — 681 modules

```
account                                     account_add_gln
account_check_printing                      account_debit_note
account_edi                                 account_edi_proxy_client
account_edi_ubl_cii                         account_fleet
account_online_payment                      account_payment
account_peppol                              account_peppol_advanced_fields
account_qr_code_emv                         account_qr_code_sepa
account_tax_python                          account_test
account_update_tax_tags                     ai_fields
ai_server_actions                           analytic
api_doc                                     attachment_indexation
auth_ldap                                   auth_oauth
auth_passkey                                auth_passkey_portal
auth_password_policy                        auth_password_policy_portal
auth_password_policy_signup                 auth_signup
auth_timeout                                auth_totp
auth_totp_mail                              auth_totp_portal
barcodes                                    barcodes_gs1_nomenclature
base                                        base_address_extended
base_automation                             base_geolocalize
base_iban                                   base_import
base_import_module                          base_install_request
base_setup                                  base_sparse_field
base_vat                                    board
bus                                         calendar
calendar_sms                                cloud_storage
cloud_storage_azure                         cloud_storage_google
cloud_storage_migration                     contacts
crm                                         crm_iap_enrich
crm_iap_mine                                crm_livechat
crm_mail_plugin                             crm_sms
data_recycle                                delivery
delivery_mondialrelay                       delivery_stock_picking_batch
digest                                      equity
event                                       event_booth
event_booth_sale                            event_crm
event_crm_sale                              event_product
event_sale                                  event_sms
fleet                                       gamification
gamification_sale_crm                       google_account
google_address_autocomplete                 google_calendar
google_gmail                                google_recaptcha
hr                                          hr_attendance
hr_calendar                                 hr_expense
hr_expense_stripe                           hr_expense_stripe_demo
hr_fleet                                    hr_gamification
hr_holidays                                 hr_holidays_attendance
hr_holidays_homeworking                     hr_homeworking
hr_homeworking_calendar                     hr_hourly_cost
hr_livechat                                 hr_maintenance
hr_org_chart                                hr_presence
hr_recruitment                              hr_recruitment_skills
hr_recruitment_sms                          hr_recruitment_survey
hr_skills                                   hr_skills_event
hr_skills_slides                            hr_skills_survey
hr_timesheet                                hr_timesheet_attendance
hr_work_entry                               hr_work_entry_holidays
html_builder                                html_editor
http_routing                                iap
iap_crm                                     iap_mail
im_livechat                                 iot_base
iot_box_image                               iot_drivers
l10n_account_edi_ubl_cii_tests              l10n_account_withholding_tax
l10n_account_withholding_tax_pos            l10n_ae
l10n_ae_pos                                 l10n_anz_ubl_pint
l10n_ar                                     l10n_ar_pos
l10n_ar_stock                               l10n_ar_website_sale
l10n_ar_withholding                         l10n_at
l10n_au                                     l10n_bd
l10n_be                                     l10n_be_pos_restaurant
l10n_be_pos_sale                            l10n_bf
l10n_bg                                     l10n_bg_ledger
l10n_bh                                     l10n_bj
l10n_bo                                     l10n_br
l10n_br_sales                               l10n_br_website_sale
l10n_ca                                     l10n_cd
l10n_cf                                     l10n_cg
l10n_ch                                     l10n_ch_pos
l10n_ci                                     l10n_cl
l10n_cm                                     l10n_cn
l10n_cn_city                                l10n_co
l10n_co_pos                                 l10n_cr
l10n_cy                                     l10n_cz
l10n_de                                     l10n_din5008
l10n_din5008_expense                        l10n_din5008_purchase
l10n_din5008_repair                         l10n_din5008_sale
l10n_din5008_stock                          l10n_dk
l10n_dk_nemhandel                           l10n_dk_oioubl
l10n_do                                     l10n_dz
l10n_ec                                     l10n_ec_edi (OPL-1)
l10n_ec_edi_stock (OPL-1)                   l10n_ec_reports (OPL-1)
l10n_ec_reports_ats (OPL-1)                 l10n_ec_sale
l10n_ec_stock                               l10n_ee
l10n_eg                                     l10n_eg_edi_eta
l10n_es                                     l10n_es_edi_facturae
l10n_es_edi_sii                             l10n_es_edi_tbai
l10n_es_edi_tbai_pos                        l10n_es_edi_verifactu
l10n_es_edi_verifactu_pos                   l10n_es_pos
l10n_et                                     l10n_eu_oss
l10n_fi                                     l10n_fi_sale
l10n_fr                                     l10n_fr_account
l10n_fr_facturx_chorus_pro                  l10n_fr_hr_holidays
l10n_fr_hr_work_entry_holidays              l10n_fr_pos_cert
l10n_ga                                     l10n_gcc_invoice
l10n_gcc_invoice_stock_account              l10n_gcc_pos
l10n_gn                                     l10n_gq
l10n_gr                                     l10n_gr_edi
l10n_gt                                     l10n_gt_edi
l10n_gw                                     l10n_hk
l10n_hn                                     l10n_hr
l10n_hr_kuna                                l10n_hu
l10n_hu_edi                                 l10n_id
l10n_id_efaktur_coretax                     l10n_id_pos
l10n_ie                                     l10n_il
l10n_in                                     l10n_in_edi
l10n_in_ewaybill                            l10n_in_ewaybill_irn
l10n_in_ewaybill_stock                      l10n_in_hr_holidays
l10n_in_pos                                 l10n_in_purchase_stock
l10n_in_sale                                l10n_in_sale_stock
l10n_in_stock                               l10n_iq
l10n_it                                     l10n_it_edi
l10n_it_edi_doi                             l10n_it_edi_sale
l10n_it_riba                                l10n_it_stock_ddt
l10n_jo                                     l10n_jo_edi
l10n_jp                                     l10n_jp_ubl_pint
l10n_ke                                     l10n_ke_edi_tremol
l10n_kh                                     l10n_km
l10n_kr                                     l10n_kw
l10n_kz                                     l10n_latam_base
l10n_latam_check                            l10n_latam_invoice_document
l10n_lb_account                             l10n_lk
l10n_lt                                     l10n_lu
l10n_lv                                     l10n_ma
l10n_mc                                     l10n_ml
l10n_mn                                     l10n_mr
l10n_mt                                     l10n_mt_pos
l10n_mu_account                             l10n_mx
l10n_my                                     l10n_my_edi
l10n_my_edi_pos                             l10n_my_ubl_pint
l10n_mz                                     l10n_ne
l10n_ng                                     l10n_nl
l10n_no                                     l10n_nz
l10n_om                                     l10n_pa
l10n_pe                                     l10n_pe_pos
l10n_ph                                     l10n_pk
l10n_pl                                     l10n_pl_edi
l10n_pt                                     l10n_qa
l10n_ro                                     l10n_ro_cpv_code
l10n_ro_edi                                 l10n_ro_edi_stock
l10n_ro_edi_stock_batch                     l10n_rs
l10n_rs_edi                                 l10n_rw
l10n_sa                                     l10n_sa_edi
l10n_sa_edi_pos                             l10n_sa_pos
l10n_sa_withholding_tax                     l10n_se
l10n_sg                                     l10n_sg_ubl_pint
l10n_si                                     l10n_sk
l10n_sn                                     l10n_syscohada
l10n_td                                     l10n_test_pos_qr_payment
l10n_test_website_sale                      l10n_tg
l10n_th                                     l10n_tn
l10n_tr                                     l10n_tr_nilvera
l10n_tr_nilvera_edispatch                   l10n_tr_nilvera_einvoice
l10n_tr_nilvera_einvoice_extended           l10n_tw
l10n_tw_edi_ecpay                           l10n_tw_edi_ecpay_website_sale
l10n_tz_account                             l10n_ua
l10n_ug                                     l10n_uk
l10n_us                                     l10n_us_account
l10n_uy                                     l10n_uy_pos
l10n_ve                                     l10n_vn
l10n_vn_edi_viettel                         l10n_za
l10n_zm_account                             link_tracker
loyalty                                     lunch
mail                                        mail_bot
mail_bot_hr                                 mail_group
mail_plugin                                 maintenance
marketing_card                              mass_mailing
mass_mailing_crm                            mass_mailing_crm_sms
mass_mailing_event                          mass_mailing_event_sms
mass_mailing_event_track                    mass_mailing_event_track_sms
mass_mailing_sale                           mass_mailing_sale_sms
mass_mailing_slides                         mass_mailing_sms
mass_mailing_themes                         microsoft_account
microsoft_calendar                          microsoft_outlook
mrp                                         mrp_account
mrp_landed_costs                            mrp_product_expiry
mrp_repair                                  mrp_subcontracting
mrp_subcontracting_account                  mrp_subcontracting_dropshipping
mrp_subcontracting_landed_costs             mrp_subcontracting_purchase
mrp_subcontracting_repair                   onboarding
partner_autocomplete                        partnership
payment                                     payment_adyen
payment_aps                                 payment_asiapay
payment_authorize                           payment_buckaroo
payment_custom                              payment_demo
payment_dpo                                 payment_flutterwave
payment_iyzico                              payment_mercado_pago
payment_mollie                              payment_nuvei
payment_paymob                              payment_paypal
payment_razorpay                            payment_redsys
payment_stripe                              payment_toss_payments
payment_worldline                           payment_xendit
phone_validation                            point_of_sale
portal                                      portal_rating
pos_account_tax_python                      pos_adyen
pos_discount                                pos_dpopay
pos_edi_ubl                                 pos_event
pos_event_sale                              pos_glory_cash
pos_hr                                      pos_hr_restaurant
pos_imin                                    pos_loyalty
pos_mercado_pago                            pos_mollie
pos_mrp                                     pos_online_payment
pos_online_payment_self_order               pos_pine_labs
pos_qfpay                                   pos_razorpay
pos_repair                                  pos_restaurant
pos_restaurant_adyen                        pos_restaurant_loyalty
pos_restaurant_stripe                       pos_sale
pos_sale_loyalty                            pos_sale_margin
pos_self_order                              pos_self_order_adyen
pos_self_order_pine_labs                    pos_self_order_qfpay
pos_self_order_razorpay                     pos_self_order_sale
pos_self_order_stripe                       pos_sms
pos_stripe                                  pos_viva_com
privacy_lookup                              product
product_email_template                      product_expiry
product_margin                              product_matrix
project                                     project_account
project_hr_expense                          project_mail_plugin
project_mrp                                 project_mrp_account
project_mrp_sale                            project_mrp_stock_landed_costs
project_mrp_workorder_account               project_purchase
project_purchase_stock                      project_sale_expense
project_sms                                 project_stock
project_stock_account                       project_stock_landed_costs
project_timesheet_holidays                  project_todo
purchase                                    purchase_edi_ubl_bis3
purchase_mrp                                purchase_product_matrix
purchase_repair                             purchase_requisition
purchase_requisition_sale                   purchase_requisition_stock
purchase_stock                              rating
repair                                      resource
resource_mail                               rpc
sale                                        sale_crm
sale_edi_ubl                                sale_expense
sale_expense_margin                         sale_gelato
sale_gelato_stock                           sale_loyalty
sale_loyalty_delivery                       sale_management
sale_margin                                 sale_mrp
sale_mrp_margin                             sale_pdf_quote_builder
sale_product_matrix                         sale_project
sale_project_stock                          sale_project_stock_account
sale_purchase                               sale_purchase_project
sale_purchase_stock                         sale_renting_project
sale_service                                sale_sms
sale_stock                                  sale_stock_margin
sale_stock_product_expiry                   sale_timesheet
sale_timesheet_margin                       sales_team
sms                                         sms_twilio
snailmail                                   snailmail_account
social_media                                spreadsheet
spreadsheet_account                         spreadsheet_dashboard
spreadsheet_dashboard_account               spreadsheet_dashboard_event_sale
spreadsheet_dashboard_hr_expense            spreadsheet_dashboard_hr_timesheet
spreadsheet_dashboard_im_livechat           spreadsheet_dashboard_marketing_automation
spreadsheet_dashboard_pos_hr                spreadsheet_dashboard_pos_restaurant
spreadsheet_dashboard_sale                  spreadsheet_dashboard_sale_timesheet
spreadsheet_dashboard_stock_account         spreadsheet_dashboard_website_sale
spreadsheet_dashboard_website_sale_slides   stock
stock_account                               stock_delivery
stock_dropshipping                          stock_fleet
stock_landed_costs                          stock_maintenance
stock_picking_batch                         stock_sms
survey                                      survey_crm
test_access_rights                          test_action_bindings
test_ai_fields                              test_assetsbundle
test_auth_custom                            test_base_automation
test_convert                                test_converter
test_crm_full                               test_data_module
test_data_module_install                    test_discuss_full
test_event_full                             test_event_full_enterprise
test_html_field_history                     test_http
test_import_export                          test_inherit
test_inherit_depends                        test_inherits
test_inherits_depends                       test_lint
test_mail                                   test_mail_full
test_mail_sms                               test_main_flows
test_mass_mailing                           test_mimetypes
test_orm                                    test_read_group
test_resource                               test_rpc
test_sale_product_configurators             test_sale_purchase_edi_ubl
test_search_panel                           test_spreadsheet
test_testing_utilities                      test_themes
test_translation_import                     test_uninstall
test_website                                test_website_modules
test_website_slides_full                    test_whatsapp
theme_anelusia                              theme_artists
theme_avantgarde                            theme_aviato
theme_beauty                                theme_bewise
theme_bistro                                theme_bookstore
theme_buzzy                                 theme_clean
theme_cobalt                                theme_common
theme_default                               theme_enark
theme_graphene                              theme_kea
theme_kiddo                                 theme_loftspace
theme_monglia                               theme_nano
theme_notes                                 theme_odoo_experts
theme_orchid                                theme_paptic
theme_real_estate                           theme_test_custo
theme_treehouse                             theme_vehicle
theme_yes                                   theme_zap
transifex                                   uom
utm                                         web
web_hierarchy                               web_studio_ai_fields
web_tour                                    web_unsplash
website                                     website_blog
website_cf_turnstile                        website_crm
website_crm_iap_reveal                      website_crm_livechat
website_crm_partner_assign                  website_crm_sms
website_customer                            website_event
website_event_booth                         website_event_booth_exhibitor
website_event_booth_sale                    website_event_booth_sale_exhibitor
website_event_crm                           website_event_exhibitor
website_event_sale                          website_event_track
website_event_track_live                    website_event_track_live_quiz
website_event_track_quiz                    website_forum
website_google_map                          website_hr_recruitment
website_hr_recruitment_livechat             website_links
website_livechat                            website_mail
website_mail_group                          website_mass_mailing
website_mass_mailing_sms                    website_partner
website_payment                             website_profile
website_project                             website_sale
website_sale_autocomplete                   website_sale_collect
website_sale_collect_wishlist               website_sale_comparison
website_sale_comparison_wishlist            website_sale_gelato
website_sale_loyalty                        website_sale_mass_mailing
website_sale_mondialrelay                   website_sale_mrp
website_sale_slides                         website_sale_stock
website_sale_stock_wishlist                 website_sale_wishlist
website_slides                              website_slides_forum
website_slides_survey                       website_sms
website_timesheet
```

> **Note:** 4 Ecuador modules (`l10n_ec_edi`, `l10n_ec_edi_stock`, `l10n_ec_reports`, `l10n_ec_reports_ats`) use the `OPL-1` (Odoo Proprietary License) — a third license type distinct from both OEEL-1 and LGPL-3.

---

## Key System Parameters

| Parameter | Description |
|---|---|
| `database.uuid` | Unique database identifier |
| `database.enterprise_code` | The subscription code entered by the user |
| `database.expiration_date` | When the license expires |
| `database.expiration_reason` | Why it expires (`trial`, `demo`, `renewal`, `upsell`) |
| `database.already_linked_subscription_url` | URL shown when subscription is linked to another DB |
| `database.already_linked_email` | Email of the subscription owner |
| `database.already_linked_send_mail_url` | URL to request unlinking |
| `sysadmin.message` | JSON with custom admin messages from Odoo's server |

---

## Bypass Points

### 1. Disable the Cron Job (Weekly Server Ping)

**File:** `odoo/addons/mail/data/ir_cron_data.xml`

The cron job "Publisher: Update Notification" runs weekly and POSTs database info to Odoo's servers. The response updates the system parameters (expiration date, reason, etc.).

**How to block (two layers for defense-in-depth):**

**Layer 1 — Deactivate the cron:** Set `active` to `False` so Odoo's scheduler never triggers it.

**Layer 2 — Comment the code:** Change the `code` field to a Python comment so that even if someone re-activates the cron from the UI, it executes nothing. The `code` field is evaluated via `safe_eval`, so `#model.update_notification(None)` is a valid no-op.

```xml
<!-- odoo/addons/mail/data/ir_cron_data.xml, line 15 -->
<!-- Original record id is: ir_cron_module_update_notification -->
<record id="ir_cron_module_update_notification" model="ir.cron">
    <field name="name">Publisher: Update Notification</field>
    <field name="model_id" ref="model_publisher_warranty_contract"/>
    <field name="state">code</field>
    <field name="code">#model.update_notification(None)</field>  <!-- LAYER 2: commented out -->
    <field name="user_id" ref="base.user_root" />
    <field name="interval_number">1</field>
    <field name="interval_type">weeks</field>
    <field name="nextcall" eval="(DateTime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')" />
    <field name="active" eval="False"/>                          <!-- LAYER 1: deactivated -->
    <field name="priority">1000</field>
</record>
```

**Effect:** Stops the weekly ping to `services.odoo.com/publisher-warranty/`. Without this, the server can no longer update expiration dates or push sysadmin messages. The double-layer approach ensures resilience even if the cron is accidentally re-enabled.

---

### 2. Block Server Communication

**File:** `odoo/addons/mail/models/update.py`

The method `_get_sys_logs()` performs the actual HTTP POST to Odoo's publisher warranty server. The method `update_notification()` processes the response and updates system parameters.

> **Scope clarification:** This change **ONLY affects the license ping**. The model
> `publisher_warranty.contract` is a standalone abstract model with no connection to any other
> Odoo functionality. It does not affect:
>
> - **Email sending** — handled by `mail.mail` cron (`process_email_queue`)
> - **Email fetching** — handled by `fetchmail.server` cron (`_fetch_mails`)
> - **Message scheduling** — handled by `mail.scheduled_message` / `mail.message_schedule` crons
> - **API endpoints** — handled by their own controllers
> - **Any other cron job** — each uses its own independent model and method
>
> All crons are defined in `odoo/addons/mail/data/ir_cron_data.xml` and target completely
> separate models. Blocking `publisher_warranty.contract` touches **nothing else**.

**How to block:**
- Make `_get_sys_logs()` return an empty/mocked response:

```python
# odoo/addons/mail/models/update.py
# In the publisher_warranty_contract class:

def _get_sys_logs(self):
    # Return a mocked empty response instead of contacting the server
    return {
        "messages": [],
        "enterprise_info": {},
    }
```

- Alternatively, make `update_notification()` a no-op:

```python
def update_notification(self, cron_mode=True):
    return  # Do nothing
```

**Effect:** Even if the cron fires (or a user triggers "Check Status"), no data is sent to Odoo and no parameters are overwritten.

---

### 3. Block the Frontend Expiration Panel

**Files:**
- `odoo/addons/web_enterprise/static/src/webclient/home_menu/enterprise_subscription_service.js`
- `odoo/addons/web_enterprise/static/src/webclient/home_menu/expiration_panel.js`
- `odoo/addons/web_enterprise/static/src/webclient/home_menu/expiration_panel.xml`

The `enterpriseSubscriptionService` reads `session.expiration_date` and computes `daysLeft`. The `ExpirationPanel` component renders a warning banner in the home menu when `daysLeft <= 30`.

**How to block:**

Option A — Force `daysLeft` to always be high in the service:

```javascript
// enterprise_subscription_service.js
// In the constructor or getter for daysLeft:
get daysLeft() {
    return 9999; // Always appear valid
}
```

Option B — Make the panel never visible in the template:

```xml
<!-- expiration_panel.xml -->
<!-- Wrap the root element with t-if="false" -->
<t t-if="false">
    <!-- ... entire panel content ... -->
</t>
```

**Effect:** The warning banner (blue/yellow/red) never appears in the home menu.

---

### 4. Block the Expired UI Blocker

**File:** `odoo/addons/web_enterprise/static/src/webclient/home_menu/expiration_panel.js`

When `daysLeft <= 0`, the `ExpiredSubscriptionBlockUI` component is registered in the `main_components` registry. This creates a full-screen overlay that blocks all interaction with the application.

**How to block:**

Remove or comment out the registry entry:

```javascript
// expiration_panel.js — find and remove/comment this line:
// registry.category("main_components").add("ExpiredSubscriptionBlockUI", { ... });
```

Or make it conditional so it never activates:

```javascript
// Replace the component's setup so it never renders
class ExpiredSubscriptionBlockUI extends Component {
    static template = xml`<t/>`;  // Empty template — renders nothing
    static props = { "*": true };
}
```

**Effect:** Even if the license is expired (`daysLeft <= 0`), the UI remains fully usable — no blocking overlay appears.

---

### 5. Fake the System Parameters

**Target:** `ir.config_parameter` records in the database.

The license state is ultimately stored as key-value pairs in the `ir_config_parameter` table. By setting these to valid values and preventing them from being overwritten (see points 1–2), the system believes the license is active.

**How to block:**

Via SQL directly on the database:

```sql
-- Set expiration far in the future
INSERT INTO ir_config_parameter (key, value, create_uid, create_date, write_uid, write_date)
VALUES ('database.expiration_date', '2099-12-31 23:59:59', 1, NOW(), 1, NOW())
ON CONFLICT (key) DO UPDATE SET value = '2099-12-31 23:59:59', write_date = NOW();

-- Set a valid-looking reason (empty or 'renewal' means normal subscription)
INSERT INTO ir_config_parameter (key, value, create_uid, create_date, write_uid, write_date)
VALUES ('database.expiration_reason', 'renewal', 1, NOW(), 1, NOW())
ON CONFLICT (key) DO UPDATE SET value = 'renewal', write_date = NOW();

-- Clear any linked-subscription conflicts
DELETE FROM ir_config_parameter WHERE key IN (
    'database.already_linked_subscription_url',
    'database.already_linked_email',
    'database.already_linked_send_mail_url'
);
```

Or via Odoo shell:

```python
self.env['ir.config_parameter'].sudo().set_param('database.expiration_date', '2099-12-31 23:59:59')
self.env['ir.config_parameter'].sudo().set_param('database.expiration_reason', 'renewal')
```

**Effect:** The system reads a far-future expiration date and considers the license valid. Combined with disabling the cron (point 1) or blocking communication (point 2), these values won't be overwritten.

---

## Recommended Minimal Combination

For a complete bypass, combine:

| Point | Purpose | Required? |
|---|---|---|
| **#1 or #2** | Prevent server from resetting parameters | Yes — pick one |
| **#5** | Set a valid far-future expiration | Yes |
| **#4** | Safety net — prevent UI block even if params fail | Recommended |
| **#3** | Hide the warning banner entirely | Optional (cosmetic) |

The minimum is **#1 + #5** (disable cron + fake parameters). Adding **#4** provides a fallback if parameters are somehow reset.

---

## 6. Block All IAP & OdooFin Outbound Calls

Two source files were modified to block **all outbound calls to Odoo-controlled servers**.
Instead of contacting Odoo's servers, they raise a user-friendly error:

> Servicio no disponible, contacta con soporte para habilitarlo.
> Service not available, contact support to enable it.

### Why direct source modification (not a module)

A monkey-patching module was considered but rejected because **9 modules import `iap_jsonrpc`
directly** (e.g., `from odoo.addons.iap.tools.iap_tools import iap_jsonrpc`). In Python, a
direct import creates a new binding — monkey-patching the module attribute does NOT affect
callers that already hold a reference to the original function. Modifying the function body
directly in the source file is the only 100% reliable approach.

### Changes applied

**File 1: `odoo/addons/iap/tools/iap_tools.py`** — `iap_jsonrpc()` function

This is the single entry point for ALL IAP services. Every module below calls this function,
regardless of how they import it:

| Blocked Service | Endpoint | Module |
|---|---|---|
| Invoice/Expense/Bank Statement OCR | `extract.api.odoo.com` | `account_invoice_extract`, `hr_expense_extract`, etc. |
| SMS Sending | `sms.api.odoo.com` | `sms` |
| Physical Mail (Snailmail) | `iap-snailmail.odoo.com` | `snailmail` |
| Partner Autocomplete | `partner-autocomplete.odoo.com` | `partner_autocomplete` |
| Lead Mining | `iap-services.odoo.com` | `crm_iap_mine` |
| Lead Enrichment | `iap-services.odoo.com` | `iap` (enrich API) |
| Website Visitor Reveal | `iap-services.odoo.com` | `website_crm_iap_reveal` |
| Currency Rate Live | `iap-services.odoo.com` | `currency_rate_live` |
| Amazon Sales Channel | `iap-services.odoo.com` | `sale_amazon` |
| IAP Account Balance | `iap.odoo.com` | `iap` |
| Website Generator AI | `iap-services.odoo.com` | `website_generator` |
| Google Reserve | `iap-services.odoo.com` | `appointment_google_reserve` |
| Mobile Push Notifications | `iap-services.odoo.com` | `mail_mobile` |
| Brazil Tax (Avatax) | `iap-services.odoo.com` | `l10n_br_avatax` |
| Swiss Payroll | `iap-services.odoo.com` | `l10n_ch_hr_payroll` |
| Peru EDI | `iap-services.odoo.com` | `l10n_pe_edi` |
| Denmark Tax Reports | `iap-services.odoo.com` | `l10n_dk_reports` |
| France Reports | `iap-services.odoo.com` | `l10n_fr_reports` |
| Sign (emsigner/itsme) | `iap-services.odoo.com` | `sign_emsigner`, `sign_itsme` |
| India IAP | `iap-services.odoo.com` | `l10n_in` |
| Germany/Austria POS Cert | `iap-services.odoo.com` | `l10n_de_pos_cert`, `l10n_at_pos` |
| Belgium CODA Clean | `iap-services.odoo.com` | `l10n_be_codaclean` |
| CRM Business Card Scanner | `iap-services.odoo.com` | `crm_enterprise` |
| Social Push Notifications | `iap-services.odoo.com` | `social_push_notifications` |

**File 2: `odoo/addons-enterprise/account_online_synchronization/models/account_online.py`** — `_fetch_odoo_fin()`

This is the only service that bypasses `iap_jsonrpc` and uses direct `requests.post`:

| Blocked Service | Endpoint | Module |
|---|---|---|
| Bank Synchronization | `production.odoofin.com` | `account_online_synchronization` |

### What data is NO LONGER sent to Odoo

With these changes, the following data stays local:

- `database.uuid` (your permanent installation fingerprint)
- Document contents (invoices, receipts, bank statements, CVs)
- SMS messages and phone numbers
- Company data, user emails, search queries
- Bank credentials and transaction data
- Lead/contact enrichment queries

---

## Session Info Flow (Reference)

The file `odoo/addons/web_enterprise/models/ir_http.py` injects license data into every session:

```
User logs in
  → ir.http.session_info()
    → Checks user group:
        - base.group_system → warning: "admin"
        - Internal user     → warning: "user"
        - Portal/public     → warning: False (no checks)
    → Reads ir.config_parameter:
        - database.expiration_date
        - database.expiration_reason
        - sysadmin.message
    → Returns in session_info dict
      → Frontend reads and displays accordingly
```
