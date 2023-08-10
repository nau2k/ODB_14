# -*- coding: utf-8 -*-
import pytz
from odoo import models, fields, api, _

ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id')

@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

# put POSIX 'Etc/*' entries at the end to avoid confusing users - see bug 1086728
_tzs = [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]
def _tz_get(self):
    return _tzs

class WizardMakeContact(models.Model):
    _name = 'wizard.make.contact'
    _description = 'Wizard Make Contact'

    def _default_category(self):
        return self.env['res.partner.category'].browse(self._context.get('category_id'))

    name = fields.Char(index=True)
    date = fields.Date(index=True)
    title = fields.Many2one('res.partner.title')
    parent_id = fields.Many2one('res.partner', string='Related Company', index=True)
    parent_name = fields.Char(related='parent_id.name', readonly=True, string='Parent name')
    child_ids = fields.One2many('res.partner', 'parent_id', string='Contact', domain=[('active', '=', True)])  # force "active_test" domain to bypass _search() override
    ref = fields.Char(string='Reference', index=True)
    lang = fields.Selection(_lang_get, string='Language',
                            help="All the emails and documents sent to this contact will be translated in this language.")
    active_lang_count = fields.Integer()
    tz = fields.Selection(_tz_get, string='Timezone', default=lambda self: self._context.get('tz'),
                          help="When printing documents and exporting/importing data, time values are computed according to this timezone.\n"
                               "If the timezone is not set, UTC (Coordinated Universal Time) is used.\n"
                               "Anywhere else, time values are computed according to the time offset of your web client.")

    tz_offset = fields.Char(string='Timezone offset', invisible=True)
    user_id = fields.Many2one('res.users', string='Salesperson',
      help='The internal user in charge of this contact.')
    vat = fields.Char(string='Tax ID', index=True, help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.")
    same_vat_partner_id = fields.Many2one('res.partner', string='Partner with same Tax ID', store=False)
    bank_ids = fields.One2many('res.partner.bank', 'partner_id', string='Banks')
    website = fields.Char('Website Link')
    comment = fields.Text(string='Notes')

    category_id = fields.Many2many('res.partner.category', column1='partner_id',
                                    column2='category_id', string='Tags', default=_default_category)
    credit_limit = fields.Float(string='Credit Limit')
    active = fields.Boolean(default=True)
    employee = fields.Boolean(help="Check this box if this contact is an Employee.")
    employee_id = fields.Many2one('hr.employee', string='Employee')
    function = fields.Char(string='Job Position')
    type = fields.Selection(
        [('contact', 'Contact'),
         ('invoice', 'Invoice Address'),
         ('delivery', 'Delivery Address'),
         ('other', 'Other Address'),
         ("private", "Private Address"),
        ], string='Address Type',
        default='contact',
        help="Invoice & Delivery addresses are used in sales orders. Private addresses are only visible by authorized users.")
    # address fields
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    partner_latitude = fields.Float(string='Geo Latitude', digits=(16, 5))
    partner_longitude = fields.Float(string='Geo Longitude', digits=(16, 5))
    email = fields.Char()
    email_formatted = fields.Char('Formatted Email', help='Format email address "Name <email@domain>"')
    phone = fields.Char()
    mobile = fields.Char()
    is_company = fields.Boolean(string='Is a Company', default=False,
        help="Check if the contact is a company, otherwise it is a person")
    industry_id = fields.Many2one('res.partner.industry', 'Industry')
    # company_type is only an interface field, do not use it in business logic
    company_type = fields.Selection(string='Company Type', selection=[('person', 'Individual'), ('company', 'Company')])
    company_id = fields.Many2one('res.company', 'Company', index=True)
    color = fields.Integer(string='Color Index', default=0)
    user_ids = fields.One2many('res.users', 'partner_id', string='Users', auto_join=True)
    partner_share = fields.Boolean(
        'Share Partner', store=True,
        help="Either customer (not a user), either shared user. Indicated the current partner is a customer without "
             "access or with a limited access created for sharing data.")
    contact_address = fields.Char(string='Complete Address')


    # technical field used for managing commercial fields
    commercial_partner_id = fields.Many2one('res.partner', string='Commercial Entity', store=True, index=True)
    commercial_company_name = fields.Char('Company Name Entity', store=True)
    company_name = fields.Char('Company Name')
    barcode = fields.Char(help="Use a barcode to identify this contact.", copy=False, company_dependent=True)
    is_internal = fields.Boolean(string='Is Internal')

    @api.model
    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return list(ADDRESS_FIELDS)

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        # return values in result, as this method is used by _fields_sync()
        if not self.parent_id:
            return
        result = {}
        partner = self._origin
        if partner.parent_id and partner.parent_id != self.parent_id:
            result['warning'] = {
                'title': _('Warning'),
                'message': _('Changing the company of a contact should only be done if it '
                             'was never correctly set. If an existing contact starts working for a new '
                             'company then a new contact should be created under that new '
                             'company. You can use the "Discard" button to abandon this change.')}
        if partner.type == 'contact' or self.type == 'contact':
            # for contacts: copy the parent address, if set (aka, at least one
            # value is set in the address: otherwise, keep the one from the
            # contact)
            address_fields = self._address_fields()
            if any(self.parent_id[key] for key in address_fields):
                def convert(value):
                    return value.id if isinstance(value, models.BaseModel) else value
                result['value'] = {key: convert(self.parent_id[key]) for key in address_fields}
        return result

    def create_contact(self):
        contact_vals = {
            'name': self.name,
            'employee_id': self.employee_id.id,
            'employee': self.employee,
            'is_internal': self.is_internal,
            'is_company': self.is_company,
            'type': self.type,
            'company_type': self.company_type,
            'function': self.function,
            'lang': self.lang,
            'parent_id': self.parent_id.id,
            'website': self.website,
            'phone': self.phone,
            'email': self.email,
            'company_id': self.company_id.id if self.company_id else False,
            'title': self.title.id,
            'country_id': self.country_id.id,
            'state_id': self.state_id.id,
            'zip': self.zip,
            'city': self.city,
            'street': self.street,
            'street2': self.street2,
        }

        partner_id = self.env['res.partner'].create(contact_vals)
        self.employee_id.write({'address_home_id': partner_id.id})