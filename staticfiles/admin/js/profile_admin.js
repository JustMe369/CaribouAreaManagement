document.addEventListener('DOMContentLoaded', function() {
    (function($) {
        $(document).ready(function() {
            var roleSelect = $('#id_role');
            var storesRow = $('.form-row.field-stores');

            function toggleStoresRow() {
                if (roleSelect.val() === 'visit_creator') {
                    storesRow.hide();
                } else {
                    storesRow.show();
                }
            }

            // Initial check
            toggleStoresRow();

            // Add event listener
            roleSelect.change(toggleStoresRow);
        });
    })(django.jQuery);
});