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
//this is an adaptation of Jonathan Pyle's datereplace.js


/* Validation priority (https://design-system.service.gov.uk/components/date-input/#error-messages):
*  1. missing or incomplete information (when parent is no longer in focus, highlight fields missing info?)
*  2. information that cannot be correct (for example, the number ‘13’ in the month field)
*  3. information that fails validation for another reason
*     (note: maybe less than 4 digits in year counts? Maybe it's #2)
*/
// da doesn't log the full error sometimes, so we'll do our own try/catch
try {{
// TODO: test copy/pasting input
// TODO: Set names of inputs to same as ids of inputs, then use
// the other things that go with it, like `for`. Also, we might then
// be able to make a jQuery validation plugin `group`. Still not sure
// `group` is useful since we need to sometimes treat the fields
// individually. https://stackoverflow.com/a/14147170/14144258
// TODO: Check out `ignore: ''` https://stackoverflow.com/questions/13692061/using-the-jquery-validate-plugin-to-check-if-one-or-more-checkboxes-with-differ#comment18861816_13708252
// That might break docassemble things, though, if we can't make it specific
// to just these fields.
// TODO: Latest error message is taking precedence while all previously invalid
// fields are still red. Change that. (Beyond MVP?)
  
var priorites_date_part = {{
  empty: 1,
  out_of_range: 2,
  invalid: 3,  // Maybe non-4-digit year
}};
var priorities_full_date = {{
  // Multiple or non-determinate out of range, max, min
  out_of_range: 1,
  invalid: 2,
}};
  
  
$(document).on('daPageLoad', function(){{
  
  
  // Custom validation
  // We can't use `$("#myform").validate({{rules:{{...}} }})
  // etc. because it needs names and we don't have them here.
  $('#daform').validate({{}});
  //this is an adaptation of Jonathan Pyle's datereplace.js
    $('input[type="ALThreePartsDateTestValidation"]').each(function(){{
      var dateElement = this;
      var required = $(dateElement).closest('.da-form-group').hasClass('darequired');
      $(dateElement).hide();
      $(dateElement).attr('type', 'hidden');
      $(dateElement).attr('aria-hidden', 'true');
      
      //Construct the input components
      var parentElement = $('<div class="form-row row al_split_date_parent">');
      var almin = $(dateElement).data('almin');
      var almax = $(dateElement).data('almax');
      var almin_message = $(dateElement).data('alminmessage');
      var almax_message = $(dateElement).data('almaxmessage');
      // TODO: invalid date message. Allow dev to disable?
      // TODO: 4-digit year message. Allow dev to disable?
      
      // Avoid .data for our dynamic stuff - caching problems
      // https://forum.jquery.com/topic/jquery-data-caching-of-data-attributes
      // https://stackoverflow.com/a/8708345/14144258
      $(parentElement).attr('data-almin', almin);
      $(parentElement).attr('data-almax', almax);
      
      $(parentElement).attr('data-alminmessage', almin_message);
      $(parentElement).attr('data-almaxmessage', almax_message);
      
      var monthId = dateElement.id + '-month';
      var monthParent = $('<div class="col">');
      var monthLabel = $('<label>{{month}}</label>');
      monthLabel.attr( 'for', monthId );
      var monthElement = $('<select class="form-select al_split_date month ' + dateElement.id + '">');
      monthElement.attr( 'id', monthId );
      monthElement.attr( 'required', required );
      monthElement.prop( 'required', required );
      
      var dayId = dateElement.id + '-day';
      var dayParent = $('<div class="col">');
      var dayLabel = $('<label>{{day}}</label>');
      dayLabel.attr( 'for', dayId );
      // Reconsider type `number`
      // https://github.com/alphagov/govuk-design-system-backlog/issues/42#issuecomment-409848587
      // `inputmode` ("numeric") not fully supported yet (02/09/2023)
      // Avoid `pattern` - voice control will enter invalid input (https://github.com/alphagov/govuk-design-system-backlog/issues/42#issuecomment-775103437)
      var dayElement = $('<input class="form-control day al_split_date ' + dateElement.id + '" type="number" min="1">' );
      dayElement.attr( 'id', dayId );
      dayElement.attr( 'required', required );
      dayElement.prop( 'required', required );
      
      var yearId = dateElement.id + '-year';
      var yearParent = $('<div class="col">');
      var yearLabel = $('<label>{{year}}</label>');
      yearLabel.attr( 'for', yearId );
      //Do not restrict year input range for now.
      // Reconsider type `number`
      // https://github.com/alphagov/govuk-design-system-backlog/issues/42#issuecomment-409848587
      // `inputmode` ("numeric") not fully supported yet (02/09/2023)
      // Avoid `pattern` - voice control will enter invalid input (https://github.com/alphagov/govuk-design-system-backlog/issues/42#issuecomment-775103437)
      var yearElement = $('<input class="form-control year al_split_date ' + dateElement.id + '" type="number" min="1">');
      yearElement.attr( 'id', yearId );
      yearElement.attr( 'required', required );
      yearElement.prop( 'required', required );
      
      // TODO: try removing this
      var errorElement = $('<span id="' + dateElement.id + '-error" class="da-has-error invalid-feedback al_split_date error"></div>');
        
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
      
      // Updates will be triggered when the user leaves an input field
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
      
      // `depends` docs: https://stackoverflow.com/a/13626251/14144258 and
      // https://jqueryvalidation.org/validate/
      // TODO: the most recent error message overwrites the others. Maybe
      // help? https://stackoverflow.com/a/71957334
      $('.' + dateElement.id).each(function() {{
        let elem = this;
        $(elem).rules( 'add', {{
          _alvaliddate: true,  // Valid date
          // _al4digityear: true,  // 4-digit year
          almin: {{
            depends: function(element) {{
              return get_$parent(element).attr('data-almin') !== undefined;
            }}
          }},  // Do I even need to do `depends` if I'm doing it inside this loop?
          almax: {{
            depends: function(element) {{
              // Birthdates always have a max value
              // TODO: Should the dev still be able to override? 
              if ( is_birthdate(element) ) {{
                return true;
              }}
              // Otherwise, check the element itself
              return get_$parent(element).attr('data-almax') !== undefined;
            }}
          }},
        }});  // ends add rules
        
        // Avoid later elements overwriting messages of earlier elements by
        // adding messages dynamically. https://stackoverflow.com/a/20928765/14144258
        // `.one()` will make sure this is only set once
        $(this).one('change', function (event) {{
        
          // Add this error validation to the existing error validation
          var originalErrorPlacement = $('#daform').validate().settings.errorPlacement;
          var errorPlacement = function(error, element) {{
            // Finds an AL date parent
            var $parent = get_$parent(element);
            
            // If this isn't an AL date, use the original behavior
            if (!$parent[0]) {{
              originalErrorPlacement(error, element);
              return;
            }}
            
            // Otherwise, use our custom error labeling
            $($parent.find('span.invalid-feedback')).remove();
            // For codepen practice:
            $($parent.find('label.error')).remove();
            $(error).appendTo($parent);
            // Add class 'is-invalid', set aria-invalid to true
            // and aria-describedby to something like
            // "dGVzdF8zX3BhcnQ-year-error dGVzdF8zX3BhcnQ-month-error dGVzdF8zX3BhcnQ-day-error"
            // https://stackoverflow.com/a/53404898/14144258
            // using the three elements' `id`s.
            // TODO: In future, this should depend on what kind of invalidation
            // it is. That info could be stored in a `data` attribute
            
          }};
          // Override the previous errorPlacement
          var validator = $("#daform").data('validator');
          validator.settings.errorPlacement = errorPlacement;
          
          
          // -- Styling (see al_dates.css) --
          
          // // TODO: Remove highlight control
          // var originalHighlight = $('#daform').validate().settings.highlight;
          // var highlight = function(element, errorClass, validClass) {{
            // // Finds an AL date parent
            // var $al_parent = get_$parent(element);
            // // Highlight all of the children inputs
            // // TODO: Only do this on min/max/invalid date failures
            // $al_parent.addClass('al_invalid');
//             
            // originalHighlight(element, errorClass, validClass);
          // }};
          // // Override the previous highlight
          // var validator = $("#daform").data('validator');
          // validator.settings.highlight = highlight;
//           
          // var originalUnhighlight = $('#daform').validate().settings.unhighlight;
          // var unhighlight = function(element, errorClass, validClass) {{
            // // Finds an AL date parent
            // var $al_parent = get_$parent(element);
            // // Unhighlight all of the children inputs
            // // TODO: Only do this on min/max/invalid date failures
            // $al_parent.removeClass('al_invalid');
//             
            // originalUnhighlight(element, errorClass, validClass);
          // }};
          // // Override the previous highlight
          // var validator = $("#daform").data('validator');
          // validator.settings.unhighlight = unhighlight;
          
          // -- Messages --
          
          // IMPORTANT: If the developer can put in their own messages,
          // they will also be able to make sure that they are translated.
          
          var default_min_message = 'This date is too early.';
          var default_max_message = 'This date is too late.';
          // Birthdays have a different default max message
          if (is_birthdate(event.target)) {{
            default_max_message = 'The birthdate must be in the past.';
          }}
          
          var min_message = get_$parent(this).attr('data-alminmessage') || default_min_message;
          var max_message = get_$parent(this).attr('data-almaxmessage') || default_max_message;
          
          // Dynamically set the message
          // TODO: Do we need to ensure other messages aren't errased?
          // So far we've seen other messages still show up just fine.
          $(this).rules('add', {{
            messages: {{
              _alvaliddate: jQuery.validator.format('There cannot be that many days in this month.'),
              // _alvaliddate: function () {{
              //   // "monthname doesn't have that many days"
              // }},
              // _alyear: "",
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
    // This only handles `max`. Handle invalid date input elsewhere.
    // TODO: elsewhere add special invalidation for invalid dates
    // TODO:  need to figure out how to prioritize types of validation.
    
    var data = get_date_data(element);
    // Don't show an error if the date is only partly filled
    if (data.year == '' || data.month == '' || data.day === '') {{
      // TODO: Add a message for an incomplete date? Elsewhere.
      return true;
    }}
    var date_val = new Date(data.year + '-' + data.month + '-' + data.day);
    if ( isNaN( date_val ) ) {{
      return true;
    }}
    var $al_parent = get_$parent(element);
    // TODO: Catch invalid min dates? Useful for devs. Otherwise very hard to track down.
    var date_min = new Date($al_parent.attr('data-almin'));
    let is_valid = date_val >= date_min;
    handle_parent_validation({{ element, is_valid }});
    
    return is_valid;
  }});
  
  
  $.validator.addMethod('almax', function(value, element, params) {{
    // This only handles `max`. Handle invalid date input elsewhere.
    // TODO: special invalidation for invalid dates
    // TODO: add highlighting class to parent in here, since
    // max invalidates all
    // console.log('=== validating max ===');
    
    var data = get_date_data(element);
    // Don't show an error if the date is only partly filled
    if (data.year == '' || data.month == '' || data.day === '') {{
      return true;
    }}
    
    var date_val = new Date(data.year + '-' + data.month + '-' + data.day);
    // TODO: Will not check for 2/31/nnnn, etc.
    if (isNaN(date_val)) {{
      return true;
    }}
    var $al_parent = get_$parent(element);
    var max_attr = $al_parent.attr('data-almax')
    // TODO: Catch invalid max dates? Useful for devs, but not as useful as min.
    var date_max = new Date(max_attr);
    if ( isNaN(date_max) && is_birthdate(element)) {{
      date_max = new Date(Date.now())
    }}
    // console.log('max_attr', max_attr, 'date_max', date_max);
    // Note that a year input of "1" counts as a date of 2001
    let is_valid = date_val <= date_max;
    handle_parent_validation({{ element, is_valid }});
    
    return is_valid;
  }});
  
  
  $.validator.addMethod('required', function(value, element, params) {{
    // This is indeed taking precedence right now, but I'm not sure why
    let is_valid = $(element).val() !== '';
    handle_part_validation({{element, is_valid}});
    return is_valid;
  }});  // ends validate 'required'
  
  
  $.validator.addMethod('_alvaliddate', function(value, element, params) {{
    /** Checks if full input values cannot be converted to a matching Date object.
    *   E.g. 12/43/2000 has an invalid day. HTML doesn't do this natively.
    *   Only day inputs can create mismatching dates. */
    let validity_vals = get_date_inputs_validity(element);
    
    let is_valid = validity_vals.day === true;
    // Display invalid highlighting on day elem if needed
    if (!is_valid) {{
      let $al_parent = get_$parent(element);
      let day_elem = $al_parent.find('.day')[0];
      handle_part_validation({{
        element: day_elem,
        is_valid: is_valid,
      }});
    }}
    
    return is_valid;
  }});  // ends validate '_alvaliddate'
  
  
  function get_date_data (element) {{
    /**
    * Given an element that holds a part of the date information,
    * return the full date data as an object.
    * 
    * @returns {{year: str, month: str, day: str}}
    */
    var year_elem = get_$parent(element).find('.year')[0];
    var month_elem = get_$parent(element).find('.month')[0];
    var day_elem = get_$parent(element).find('.day')[0];
    var date_data = {{
      year: $(year_elem).val(),
      month: $(month_elem).val(),
      day: $(day_elem).val(),
    }};
    // console.log( 'date_data in get_date_date()', date_data );
    return date_data;
  }};  // Ends get_date_data()
  
  
  function get_$parent(element) {{
    /** Return the element we created to surround our date elements.
    *   Easier to maintain all in one place. */
    // `.closest()` will get the element itself if appropriate
    return $(element).closest('.al_split_date_parent');
  }};  // Ends get_$parent()
  
  
  function is_birthdate(element) {{
    /** If the element is part of a al birthdate field, returns true, otherwise false. */
    let $search_results = get_$parent(element).parent().find('.daALBirthDateTestValidation');
    return Boolean($search_results[0]);
  }};  // Ends is_birthdate()
  
  
  function handle_parent_validation({{ element, is_valid }}) {{
    /** Add appropriate classes for invalid full al date. */
    let $al_parent = get_$parent(element);
    if (is_valid) {{
      $al_parent.removeClass('al_invalid');
    }} else {{
      $al_parent.addClass('al_invalid');
    }}
  }};  // Ends handle_parent_validation()
  
  
  function handle_part_validation({{element, is_valid}}) {{
    /** Add appropriate classes for invalid al date part. */
    var $element = $(element);
    var $al_parent = get_$parent(element);
    if (is_valid) {{
      $al_parent.removeClass('al_invalid_child');
      $element.removeClass('al_invalid');
    }} else {{
      handle_parent_validation({{element, is_valid: true}});
      $al_parent.addClass('al_invalid_child');
      $element.addClass('al_invalid');
    }}
  }};  // Ends handle_part_validation()
  
  
  function get_date_inputs_validity(element) {{
    /** Given a date part element, returns a {{year, month, day}} object.
    *   Each property is true if the input is valid and false if the input
    *   is invalid. If any inputs are empty, all properties will be true.
    *   Thus the dropdown input month will always be valid
    *
    * What would make a year or month invalid? Negative numbers? That's taken care of elsewhere.
    *    If only a day can be invalid, this can be made more simple.
    *
    * Inspired by https://github.com/uswds/uswds/blob/728ba785f0c186e231a81865b0d347f38e091f96/packages/usa-date-picker/src/index.js#L735
    * 
    * @param element {{HTMLNode}} An input in the al split date picker
    * 
    * Examples:
    * 10//2000  // {{year: true, month: true, day: true}}
    * 10/10/2000  // {{year: true, month: true, day: true}}
    * 10/32/2000  // {{year: true, month: true, day: false}}
    * Only day can be invalid in this way?
    * 12/42/2000  // {{year: true, month: true, day: false}}? {{year: false, month: true, day: false}}?
    */
    var input_status = {{
      year: true, month: true, day: true,
    }};
    
    var data = get_date_data(element);
    // Don't invalidate if the date is only partly filled. Empty input fields
    // should take care of themselves
    // if (data.year == '' || data.month == '' || data.day === '') {{
    if (data.day === '') {{
      return input_status;
    }}
    
    if (parseInt(data.day) > 31) {{
      input_status.day = false;
      return input_status;
    }}
    
    // Ensure a valid date to check against, so
    // day can always be validated. Is this appropriate?
    if (data.year === '') {{data.year = 2000;}}
    if (data.month === '') {{data.month = 1;}}
    
    const dateStringParts = [data.year, data.month, data.day];
    const [year, month, day] = dateStringParts.map((str) => {{
      let value;
      const parsed = parseInt(str, 10);
      if (!Number.isNaN(parsed)) value = parsed;
      return value;
    }});
    // Would month or year ever be null?
    input_status.year = year !== null;
    input_status.month = month !== null;
    input_status.day = day !== null;
    
    // TODO: Show failing max day anytime it exists. don't wait for all input
    if (month && day && year != null) {{
      const checkDate = setDate({{
        year: year,
        month: month - 1,
        date: day
      }});
      
      // What non-'' year could cause an invalid date?
      // If month as a value, it's always valid (dropdown)
      if (
        checkDate.getFullYear() !== year ||
        checkDate.getMonth() !== (month - 1) ||
        checkDate.getDate() !== day
      ) {{
        input_status.day = false;
      }}
    }}
    
    return input_status;
  }};  // Ends get_date_inputs_validity()
  
  /**
   * Set date from month day year
   *
   * @param {{number}} year the year to set
   * @param {{number}} month the month to set (zero-indexed)
   * @param {{number}} date the date to set
   * @returns {{Date}} the set date
   */
  const setDate = ({{year, month, date}}) => {{
    const newDate = new Date(0);
    newDate.setFullYear(year, month, date);
    return newDate;
  }};
  
}});  // ends on da page load


}} catch (error) {{
  console.error('Error in AL date CusotmDataTypes', error);
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
    # Alternatively, is it possible to allow the developer to put in their own values
    # for these labels?
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
