from docassemble.base.util import (
    CustomDataType,
    DAValidationError,
    word,
    as_datetime,
    today,
    date_difference,
    log,
)
from typing import Optional
import re

js_text = """\
// da doesn't log the full error sometimes, so we'll do our own try/catch
try {{

$(document).on('daPageLoad', function(){{
  // Custom validation
  // We can't use `$("#myform").validate({{rules:{{...}} }})
  // etc. because it needs names and we don't have them here.
  $('#daform').validate({{}});

  //this is an adaptation of Jonathan Pyle's datereplace.js
    $('input[type="ALThreePartsDateTestValidation"]').each(function(){{
      var date_type = 'ALThreePartsDateTestValidation';  // Will be replaced by python
      var dateElement = this;
      var required = $(dateElement).closest('.da-form-group').hasClass('darequired');
      $(dateElement).hide();
      $(dateElement).attr('type', 'hidden');
      $(dateElement).attr('aria-hidden', 'true');
      
      //Construct the input components
      var parentElement = $('<div class="form-row row al-split-date-parent">');
      var almin = $(dateElement).data('almin');
      var almax = $(dateElement).data('almax');
      //var almax = null;
      // How is this already detecting a maximum of today?
      //// For birthdates, default max should be today
      //if ( $($(parentElement).find('.daALBirthDateTestValidation')) ) {{
      //  
      //}}
      
      var almin_message = $(dateElement).data('alminmessage');
      var almax_message = $(dateElement).data('almaxmessage');
      
      // Avoid .data for our dynamic stuff - caching problems
      // https://forum.jquery.com/topic/jquery-data-caching-of-data-attributes
      // https://stackoverflow.com/a/8708345/14144258
      $(parentElement).attr('data-almin', almin);
      $(parentElement).attr('data-almax', almax);
      
      $(parentElement).attr('data-alminmessage', almin_message);
      $(parentElement).attr('data-almaxmessage', almax_message);
      
      var monthId = dateElement.id + '-month';
      var monthParent = $('<div class="col">');
      var monthLabel = $('<label style="text-align:center">{month}</label>');
      monthLabel.attr( 'for', monthId );
      var monthElement = $('<select class="form-select al-split-date month ' + dateElement.id + '" style="width:7.5em">');
      monthElement.attr( 'id', monthId );
      monthElement.attr( 'required', required );
      monthElement.prop( 'required', required );
      
      var dayId = dateElement.id + '-day';
      var dayParent = $('<div class="col">');
      var dayLabel = $('<label style="text-align:center">{day}</label>');
      dayLabel.attr( 'for', dayId );
      // Reconsider type `number`
      var dayElement = $('<input class="form-control day al-split-date ' + dateElement.id + '" type="number" min="1" max="31">' );
      dayElement.attr( 'id', dayId );
      dayElement.attr( 'required', required );
      dayElement.prop( 'required', required );
      
      var yearId = dateElement.id + '-year';
      var yearParent = $('<div class="col">');
      var yearLabel = $('<label style="text-align:center">{year}</label>');
      yearLabel.attr( 'for', yearId );
      //Do not restrict year input range for now.
      // Reconsider type `number`
      var yearElement = $('<input class="form-control year al-split-date ' + dateElement.id + '" type="number">');
      yearElement.attr( 'id', yearId );
      yearElement.attr( 'required', required );
      yearElement.prop( 'required', required );
      
      // TODO: try removing this
      var errorElement = $('<span id="' + dateElement.id + '-error" class="da-has-error invalid-feedback al-split-date error"></div>');
        
      // If we're returning to a variable that has already been defined
      // prepare to use that variable's values
      var dateParts;
      if ( $(dateElement).val() ) {{
        dateParts = $(dateElement).val().split( '/' );
        dateParts.forEach( function( part, index, dateParts ) {{
          var partInt = parseInt( part );
          if (isNaN(partInt)) {{
            dateParts[ index ] = '';
          }} else {{
            dateParts[ index ] = partInt;
          }}
        }});
      }} else {{
        dateParts = null;
      }}
          
      // Insert previous answers if possible
      
      // -- Month --
      // "No month selected" option
      var first_opt = $("<option>");
      first_opt.val("");
      first_opt.text("");
      monthElement.append( first_opt );
      // Add every calendar month (based on user's computer's date system? lanugage?)
      var option = null
      for(var month=0; month < 12; month++) {{
        opt = $("<option>");
        if ( month < 9 ) {{
          opt.val('0' + (month + 1));
        }} else {{
          opt.val(month + 1);
        }}
        
        // Convert the month number to a month name for the option text
        var dt = new Date(1970, month, 1);
        opt.text(dt.toLocaleString('default', {{ month: 'long' }}));
        
        // Use previous values if possible
        if ( dateParts && parseInt( opt.val() ) === dateParts[ 0 ]) {{
          opt.attr('selected', 'selected');
        }}
        
        monthElement.append(opt);
      }}  // ends for every month
    
      // -- Day and year --
      // Use previous values if possible
      if ( dateParts ) {{
        dayElement.val( dateParts[ 1 ]);
        yearElement.val( dateParts[ 2 ]);
      }}
      
      // -- Add elements to DOM --
      
      $(dateElement).before(parentElement); 
      $(monthParent).append(monthLabel);
      $(monthParent).append(monthElement);
      $(parentElement).append(monthParent); 
      $(dayParent).append(dayLabel);
      $(dayParent).append(dayElement);
      $(parentElement).append(dayParent); 
      $(yearParent).append(yearLabel);
      $(yearParent).append(yearElement);
      $(parentElement).append(yearParent);
      // TODO: try removing this
      $(parentElement).append(errorElement);
      
      // -- Update on 'change' event --
      
      // Updates will be triggered when the user leave an input field
      yearElement.on('change', updateDate);
      monthElement.on('change', updateDate);
      dayElement.on('change', updateDate);
      
      // Update value of original input when values change.
      function updateDate() {{
        var data = get_date_data(parentElement);
        var date_str = data.year + '-' + data.month + '-' + data.day;
        var val = data.month + '/' + data.day + '/' + data.year;
        if ( val === '//' ) {{
          val = '';
        }}
        $(dateElement).val( val );
      }};  // Ends updateDate()
      
      // -- Validation for these elements --
      
      // TODO: I think it might be possible to use `groups`, but
      // I'm not sure how. This plugin is poorly documented.
      
      // `depends`: https://stackoverflow.com/a/13626251/14144258 and
      // https://jqueryvalidation.org/validate/
      $('.' + dateElement.id).each(function() {{
        let elem = this;
        $(elem).rules( 'add', {{
          almin: {{
            depends: function(element) {{
              return $($(element).closest('.al-split-date-parent')[0]).attr('data-almin') !== undefined;
            }}
          }},  // Do I even need to do `depends` if I'm doing it inside this loop?
          almax: {{
            depends: function(element) {{
              // Birthdates always have a max value
              //var $dates_parent = $(element).closest('.al-split-date-parent');
              //var max_attr = $dates_parent.attr('data-almax')
              //var $birthdate = $dates_parent.parent().find('.daALBirthDateTestValidation');
              if ( date_type === 'ALBirthDateTestValidation' ) {{
                // TODO next: even 3-part is always birthdate. Need different class for each?
                // Something is going on because this whole thing is run twice, once for each field.
                // because of the shared class. That said, are we going to have problems
                // when there are e.g. multiple 3-part dates on the page?
                // Use id of original class as class to loop through?
                console.log('is birthdate');
                return true;
              }}
              // Otherwise, check the element itself
              return $($(element).closest('.al-split-date-parent')[0]).attr('data-almax') !== undefined;
            }}
          }},
        }});  // ends add rules
        
        // Avoid later elements overwriting messages of earlier elements by
        // adding messages dynamically. https://stackoverflow.com/a/20928765/14144258
        // `.one()` will make sure this is only set once
        $(this).one('change', function () {{
        
          // Add this error validation to the existing error validation
          var originalErrorPlacement = $('#daform').validate().settings.errorPlacement
          var errorPlacement = function(error, element) {{
            var $parent = $(element).closest('.al-split-date-parent');
            
            // If this isn't an AL date, use the original behavior
            if ( !$parent[0] ) {{
              originalErrorPlacement(error, element);
            }}
            
            // Otherwise, use our custom error labeling
            $( $parent.find('span.invalid-feedback') ).remove();
            $(error).appendTo( $parent );
          }};
          // Override the previous errorPlacement
          var validator = $("#daform").data('validator');
          validator.settings.errorPlacement = errorPlacement;
          
          var default_min_message = 'This date is too early';
          var default_max_message = 'This date is too late';
          //// Birthdays have a different default max message
          //var $original = $($parent.find('.daALBirthDateTestValidation'));
          //if ( $($parent.find('.daALBirthDateTestValidation'))[0] ) {{
          //  default_max_message = 'The birthdate must be in the past';
          //}}
          
          //var $dates_parent = $(element).closest('.al-split-date-parent');
          //var max_attr = $dates_parent.attr('data-almax')
          //var $birthdate = $dates_parent.parent().find('.daALBirthDateTestValidation');
          
          if ( date_type === 'ALBirthDateTestValidation' ) {{
            default_max_message = 'The birthdate must be in the past';
          }}
          
          var min_message = $($(this).closest('.al-split-date-parent')[0]).attr('data-alminmessage') || default_min_message;
          var max_message = $($(this).closest('.al-split-date-parent')[0]).attr('data-almaxmessage') || default_max_message;
          
          // Dynamically set the message
          // TODO: Do we need to ensure other messages aren't errased?
          // So far we've seen other messages still show up just fine.
          $(this).rules('add', {{
            messages: {{
              almin: min_message,
              almax: max_message,
            }},
          }});
          // trigger immediate validation to update message
          $(this).valid();
        }});  // ends on change
      }});  // ends for all 3 part dates
      
      // TODO: Maybe add a message for an incomplete date when the parent loses focus
      
    }});  // ends for each input
  
  // No jQuery validation for original field, since it doesn't work on hidden
  // elements last time we tried

  $.validator.addMethod('almin', function(value, element, params) {{
    // TODO: special invalidation for invalid dates
    
    var data = get_date_data(element);
    // Don't show an error if the date is only partly filled
    if (data.year == '' || data.month == '' || data.day === '') {{
      // TODO: Add a message for an incomplete date? Elsewhere.
      return true;
    }}
    var date_val = new Date(data.year + '-' + data.month + '-' + data.day);
    var $parent = $(element).closest('.al-split-date-parent');
    var date_min = new Date($parent.attr('data-almin'));
    return date_val >= date_min;
  }});

  $.validator.addMethod('almax', function(value, element, params) {{
    // TODO: special invalidation for invalid dates
    
    var data = get_date_data(element);
    // Don't show an error if the date is only partly filled
    if (data.year == '' || data.month == '' || data.day === '') {{
      return true;
    }}
    var date_val = new Date(data.year + '-' + data.month + '-' + data.day);
    var $dates_parent = $(element).closest('.al-split-date-parent');
    var max_attr = $dates_parent.attr('data-almax')
    var date_max = new Date(max_attr);
    var $birthdate = $dates_parent.parent().find('.daALBirthDateTestValidation');
    if ( !date_max && $birthdate[0]) {{
      date_max = Date.now()
    }}
    console.log('max_attr', max_attr, 'date_max', date_max);
    // Note that a year input of "1" counts as a date of 2001
    return date_val <= date_max;
  }});

  function get_date_data (element) {{
    /**
    * Given an element that holds a part of the date information,
    * return the full date data as an object.
    * 
    * @returns {{year: str, month: str, day: str}}
    */
    // `.closest()` will get the element itself if appropriate
    var $parent = $(element).closest('.al-split-date-parent');
    var year_elem = $parent.find('.year')[0];
    var month_elem = $parent.find('.month')[0];
    var day_elem = $parent.find('.day')[0];
    var date_data = {{
      year: $(year_elem).val(),
      month: $(month_elem).val(),
      day: $(day_elem).val(),
    }};
    console.log( date_data );
    return date_data;

  }};  // Ends get_date_data()
  
  function get_$parent( element ) {{
  /** Return the element we created to surround our date elements.
  *   Easier to maintain all in one place. */
    // `.closest()` will get the element itself if appropriate
    return $(element).closest('.al-split-date-parent');
  }};  // Ends get_$parent()

}});  // ends on da page load

}} catch (error) {{
  console.error('Error in AL dates CusotmDataTypes', error);
}}
"""


def check_empty_parts(item: str, default_msg="{} is not a valid date") -> Optional[str]:
    parts = item.split("/")
    empty_parts = [part == "" for part in parts]
    if len(empty_parts) != 3:
        return word(default_msg).format(item)
    if not any(empty_parts):
        return None
    if all(empty_parts):
        return word("Enter a month, a day, and a year")
    elif sum(empty_parts) == 2:
        # only one part was given, enumerate each
        if not empty_parts[0]:
            return word("Enter a day and a year")
        elif not empty_parts[1]:
            return word("Enter a month and a year")
        else:
            return word("Enter a month and a day")
    elif sum(empty_parts) == 1:
        if empty_parts[0]:
            return word("Enter a month")
        elif empty_parts[1]:
            return word("Enter a day")
        else:
            return word("Enter a year")
    else:
        return word(default_msg).format(item)


class ALThreePartsDateTestValidation(CustomDataType):
    name = "ALThreePartsDateTestValidation"
    input_type = "ALThreePartsDateTestValidation"
    javascript = js_text.format(month=word("Month"), day=word("Day"), year=word("Year"))
    jq_message = word("Answer with a valid date")
    is_object = True
    mako_parameters = ['almin', 'almax', 'alminmessage', 'almaxmessage']

    @classmethod
    def validate(cls, item: str):
        # If there's no input in the item, it's valid
        if not isinstance(item, str) or item == "":
            return True
        else:
            # Otherwise it needs to be a date after the year 1000. We ourselves make
            # sure this format is created if the user gives valid info.
            matches_date_pattern = re.search(r"^\d{1,2}\/\d{1,2}\/\d{4}$", item)
            if matches_date_pattern:
                try:
                    date = as_datetime(item)
                except Exception as error:
                    ex_msg = f"{ item } {word('is not a valid date')}"
                    raise DAValidationError(ex_msg)
                return True
            else:
                msg = check_empty_parts(item)
                if msg:
                    raise DAValidationError(msg)

    @classmethod
    def transform(cls, item):
        if item:
            return as_datetime(item)

    @classmethod
    def default_for(cls, item):
        if item:
            return item.format("MM/dd/yyyy")


class ALBirthDateTestValidation(ALThreePartsDateTestValidation):
    name = "ALBirthDateTestValidation"
    input_type = "ALBirthDateTestValidation"
    javascript = js_text.format(
        month=word("Month"), day=word("Day"), year=word("Year")
    ).replace("ALThreePartsDateTestValidation", "ALBirthDateTestValidation")
    jq_message = word("Answer with a valid date of birth")
    is_object = True
    mako_parameters = ['almin', 'almax', 'alminmessage', 'almaxmessage']

    @classmethod
    def validate(cls, item: str):
        # If there's no input in the item, it's valid
        if not isinstance(item, str) or item == "":
            return True
        else:
            # Otherwise it needs to be a date on or before today and after the year 1000.
            # We ourselves create this format if the user gives valid info.
            matches_date_pattern = re.search(r"^\d{1,2}\/\d{1,2}\/\d{4}$", item)
            try:
                date = as_datetime(item)
            except Exception as error:
                raise DAValidationError(word("{} is not a valid date").format(item))
            if matches_date_pattern:
                date_diff = date_difference(starting=date, ending=today())
                if date_diff.days >= 0.0:
                    return True
                else:
                    raise DAValidationError(
                        word(
                            "Answer with a <strong>date of birth</strong> ({} is in the future)"
                        ).format(item)
                    )
            else:
                msg = check_empty_parts(
                    item, default_msg="{} is not a valid <strong>date of birth</strong>"
                )
                if msg:
                    raise DAValidationError(msg)
