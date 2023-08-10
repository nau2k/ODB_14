from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    # ----------------------------------------------------------
    # Selections
    # ----------------------------------------------------------

    def _attachment_location_selection(self):
        locations = self.env["ir.attachment"].storage_locations()
        return list(map(lambda location: (location, location.upper()), locations))

    # ----------------------------------------------------------
    # Database
    # ----------------------------------------------------------

    attachment_location = fields.Selection(
        selection=lambda self: self._attachment_location_selection(),
        config_parameter="ir_attachment.location",
        string="Storage Location",
        help="Attachment storage location.",
        required=True,
        default="file",
    )

    # ----------------------------------------------------------
    # Actions
    # ----------------------------------------------------------

    def action_attachment_force_storage(self):
        self.env["ir.attachment"].force_storage()
