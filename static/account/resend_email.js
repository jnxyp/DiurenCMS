$(document).ready(
    function() {
        $('#resend_email').click(
            function () {
                input = $('#{{ form.resend_validation_email.id_for_label }}');
                input.val('True');
                input[0].form.submit();
            }
        )
    }
);