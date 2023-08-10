odoo.define('erpvn_base.DataExport', function (require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var Dialog = require('web.Dialog');
var data = require('web.data');
var framework = require('web.framework');
var pyUtils = require('web.py_utils');
var DataExport = require('web.DataExport');

var QWeb = core.qweb;
var _t = core._t;
    

/**
 * Add the field in the export list
 *
 * @private
 * @param {string} fieldID
 * @param {string} label
 */

var DataExport = DataExport.include({
    _addField: function (fieldID, label) {
        var $fieldList = this.$('.o_fields_list');
        if (!$fieldList.find(".o_export_field[data-field_id='" + fieldID + "']").length) {
            $fieldList.append(
                $('<li>', {'class': 'o_export_field', 'data-field_id': fieldID}).append(
                    $('<span>', {'class': "fa fa-arrows pull-left o_short_field"}),
                    label.trim(),
                    $('<span>', {'class': 'fa fa-trash pull-right o_remove_field', 'title': _t("Remove field")})
                )
            );
        }
    },
});

return DataExport;

});
