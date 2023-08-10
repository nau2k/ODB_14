 odoo.define('erpvn_hr_work_entry.validate_work_entries', function (require) {
    "use strict";
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var session = require('web.session');

    function renderValidateShiftButton() {
        if (this.$buttons) {
            var self = this;
            this.$buttons.on('click', '.o_button_validate_work_entries', function () {
                self.do_action({
                    name: 'Batch Actions',
                    type: 'ir.actions.act_window',
                    res_model: 'wizard.validate.work.entry',
                    target: 'new',
                    views: [[false, 'form']],
                });
            });
        }
    }

    var ValidateShiftListController = ListController.extend({
        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.isgroup = false;
        },
    
        willStart: function() {
            var ready = this.buttons_template = 'ValidateWorkEntriesListView.buttons';
            // return Promise.all([this._super.apply(this, arguments), ready]);
            const acl = session.user_has_group('hr_holidays.group_hr_holidays_manager').then(hasGroup => {
                this.isgroup = hasGroup;
            });
            return Promise.all([this._super.apply(this, arguments), ready,acl]);
        },

        renderButtons: function () {
            this._super.apply(this, arguments);
            // renderValidateShiftButton.apply(this, arguments);
            if (this.isgroup) {
                renderValidateShiftButton.apply(this, arguments);
            }
            else{
                this.$buttons.find('.o_button_validate_work_entries').css({"display":"none"});
            }
            
        }
    });

    var ValidateShiftListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: ValidateShiftListController,
        }),
    });

    viewRegistry.add('validate_shift_tree', ValidateShiftListView);
});