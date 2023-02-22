from docassemble.base.util import CustomDataType, DAValidationError, word
import re

# Based on https://docassemble.org/docs/fields.html#custom%20datatype
# The parts that need to match:
# 1. `name` and the `datatype` used in the question
# 2. `input_class` and the selector used in the for loop
# 3. The `rules` key, the `rules.messages` key, and the first argument to `.addMethod()`

class AAA(CustomDataType):
    name = 'altestvalidation'
    input_class = 'da-ccc'
    input_type = 'date'
    javascript = """\
// da's try/catch doesn't log the actual error
try {
$(document).on('daPageLoad', function() {
  // Both of these destroy da custom validation messages
  //$('#daform').validate({});
  //$('#daform').validate();
  //$('#daform').validate().settings;
  //$('#daform').validate().resetForm();
  //$('#daform').valid();
  //console.log( `$('#daform').rules():`, $('#daform').rules() );

  $('.da-ccc').each(function() {
    $('#' + $(this).attr('id')).rules('add', {
      min: "2023-02-04",
      ddd: true,
      messages: {
        ddd: "ddd",
      },
    })
  });  // ends for every .da-ccc
  
  $.validator.addMethod('min', function(value, element, params){
    return new Date(value) > new Date("2023-02-04");
  });
  
  $.validator.addMethod('ddd', function(value, element, params){
    return true;
  });
});  // ends on da page load

} catch (error) {
  console.error( error );
}
"""
