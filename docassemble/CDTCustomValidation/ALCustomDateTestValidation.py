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
try {{

$(document).on('daPageLoad', function(){{
  // Custom validation
  // We can't use `$("#myform").validate({{rules:{{...}} }}) because da is already
  // using the elment `name` attribute.
  $('#daform').validate({{}});

  //this is an adaptation of Jonathan Pyle's datereplace.js
    $('input[type="ALThreePartsDateTestValidation"]').each(function(){{
      var dateElement = this;
      var required = $(dateElement).closest('.da-form-group').hasClass('darequired');
      $(dateElement).hide();
      $(dateElement).attr('type', 'hidden');
      $(dateElement).attr('aria-hidden', 'true');
      
      //Construct the input components
      var parentElement = $('<div class="form-row row al-split-date-parent">');
      var almin = $(dateElement).data('almin');
      var almax = $(dateElement).data('almax');
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
      var monthElement = $('<select class="form-select month al-split-date ' + dateElement.id + '" style="width:7.5em">');
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
              return $($(element).closest('.al-split-date-parent')[0]).attr('data-almax') !== undefined;
            }}
          }},
        }});  // ends add rules
        
        // Avoid later elements overwriting messages of earlier elements by
        // adding messages dynamically. https://stackoverflow.com/a/20928765/14144258
        $(this).on('change', function () {{
          var min_message = $($(this).closest('.al-split-date-parent')[0]).attr('data-alminmessage') || "No";
          var max_message = $($(this).closest('.al-split-date-parent')[0]).attr('data-almaxmessage') || "Not now";
          // dynamically set the message
          $(this).rules('add', {{
            messages: {{
              almin: min_message,
              almax: max_message,
            }}
          }});
          // trigger immediate validation to update message
          $(this).valid();
        }});  // ends on change
      }});  // ends for all 3 part dates
      
    }});  // ends for each input
  
// No jQuery validation for original field, since it doesn't work on hidden elements

$.validator.addMethod('almin', function(value, element, params) {{
  var data = get_date_data(element);
  if (data.year == '' || data.month == '' || data.day === '') {{
    return true
  }}
  var date_val = new Date(data.year + '-' + data.month + '-' + data.day);
  var $parent = $(element).closest('.al-split-date-parent');
  var date_min = new Date($parent.attr('data-almin'));
  return date_val >= date_min;
}});

$.validator.addMethod('almax', function(value, element, params) {{
  var data = get_date_data(element);
  if (data.year == '' || data.month == '' || data.day === '') {{
    return true
  }}
  var date_val = new Date(data.year + '-' + data.month + '-' + data.day);
  var $parent = $(element).closest('.al-split-date-parent');
  var date_max = new Date($parent.attr('data-almax'));
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
  var data = {{
    year: $(year_elem).val(),
    month: $(month_elem).val(),
    day: $(day_elem).val(),
  }};
  return data;

}};  // Ends get_date_data()

}});  // ends on da page load

}} catch (error) {{
  console.error(error);
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
