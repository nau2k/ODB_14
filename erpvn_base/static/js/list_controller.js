odoo.define('erpvn_base.list_controller', function(require) {
    "use strict";
    var core = require('web.core');
    var QWeb = core.qweb;
    var ListController = require('web.ListController');
  
    ListController.include({
        // updateButtons: function (mode) {
        //     if (this.hasButtons) {
        //         this.$buttons.toggleClass('o-editing', mode === 'edit');
        //         const state = this.model.get(this.handle, {raw: true});
        //         if (this.selectedRecords.length == 0) {
        //             this.$buttons.find('.o_list_export_xlsx').hide();
        //         } else {
        //             this.$buttons.find('.o_list_export_xlsx').show();
        //         }
        //     }
        //     this._updateSelectionBox();
        // },
        // _onSelectionChanged: function (ev) {
        //     this.selectedRecords = ev.data.selection;
        //     this.isPageSelected = ev.data.allChecked;
        //     this.isDomainSelected = false;
        //     if (this.selectedRecords.length > 0){
        //         this.$('.o_list_export_xlsx').toggle(true);
        //     }
        //     else{
        //         this.$('.o_list_export_xlsx').toggle(false);
        //     }
        //     this._updateSelectionBox();
        //     this._updateControlPanel();
        // },
    })
    return ListController;
});