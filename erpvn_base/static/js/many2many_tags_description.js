odoo.define('erpvn_base.many2many_tags_description', function (require) {
    "use strict";

    var BasicModel = require('web.BasicModel');
    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var relational_fields = require('web.relational_fields');
    var M2MTags = relational_fields.FieldMany2ManyTags;

    BasicModel.include({

        _setInvalidMany2ManyTagsDescription: function (record, fieldName) {
            var self = this;
            var localID = (record._changes && fieldName in record._changes) ?
                record._changes[fieldName] : record.data[fieldName];
            var list = this._applyX2ManyOperations(this.localData[localID]);
            var invalidDescription = [];
            _.each(list.data, function (id) {
                var record = self.localData[id];
                if (!record.data.description) {
                    invalidDescription.push(record);
                }
            });
            var def;
            if (invalidDescription.length) {
                var changes = {operation: 'DELETE', ids: _.pluck(invalidDescription, 'id')};
                def = this._applyX2ManyChange(record, fieldName, changes);
            }
            return Promise.resolve(def).then(function () {
                return {invalidDescription: _.pluck(invalidDescription, 'res_id')};
            });
        },
    });

    var FieldMany2ManyTagsDescription = M2MTags.extend({
        tag_template: "FieldMany2ManyTagsDescription",
        fieldsToFetch: _.extend({}, M2MTags.prototype.fieldsToFetch, {
            description: {type: 'char'},
        }),
        specialData: "_setInvalidMany2ManyTagsDescription",

        _render: function () {
            var self = this;
            var _super = this._super.bind(this);
            return new Promise(function (resolve, reject) {
                resolve();
            }).then(function () {
                return _super.apply(self, arguments);
            });
        },
    });

    field_registry.add('many2many_tags_description', FieldMany2ManyTagsDescription);
});