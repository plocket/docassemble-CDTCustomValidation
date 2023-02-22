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
// This is an adaptation of Jonathan Pyle's datereplace.js
// Also see https://codepen.io/plocket/pen/mdGbajy?editors=0010

// TODO: With any customdatatype of ours on the page, custom validation messages
// don't work

/* Validation priority (https://design-system.service.gov.uk/components/date-input/#error-messages):
*  1. missing or incomplete information (when parent is no longer in focus, highlight fields missing info?)
*  2. information that cannot be correct (for example, the number ‘13’ in the month field)
*     (TODO: maybe less than 4 digits in year counts? Maybe it's #3 priority?)
*  3. information that fails validation for another reason
*
* For invalidation styling see al_dates.css.
*/

/* Test:
Non-required:
1. Day: 34
2. Year: 3 (day invalid - too many days)
3. Click out (day/year invalid - 4 digits)
4. Year: 3333
5. Day: 31 (year valid, day invalid - too many days)
6. Month: Jan
7. Click out (all invalid - too late)
8. Month: none
9. Click out (all valid because incomplete)
10. Month: Jan
11. Click out (all invalid - too late)
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
// TODO: UK guidance says to add hidden text "Error:" at the beginning of a feedback
// message for screen readers.
// TODO: once one invalid field is valid, other fields that are invalid don't show
// the message of their own invalidation.
// TODO: Every field has to validate every other field too? With priority
// User bugs in da:
// I can submit the page without entering a birthdate right now. the "required" message only shows up when I start a response and then remove it
// In addition, if there's an error elsewhere on the screen, the validation error for the date field doesn't appear. so maybe something is weird with the trigger for the jquery validation.
  
  
$(document).on('daPageLoad', function(){{
  // TODO: Abstract contents so it's not as hard to see where pageload ends
  // and things can be less indented.
  
  // We can't use `$("#myform").validate({{rules:{{...}} }})
  // etc. because it needs names and we don't have them here.
  $('#daform').validate({{}});
  // TODO: unindent the below by 1
    $('input[type="ALThreePartsDateTestValidation"]').each(function(){{
      var dateElement = this;
      //var required = is_required(dateElement);
      $(dateElement).hide();
      $(dateElement).attr('type', 'hidden');
      $(dateElement).attr('aria-hidden', 'true');
      
      // -- Construct the input components --
      
      // Avoid .data for our dynamic stuff - caching problems
      // https://forum.jquery.com/topic/jquery-data-caching-of-data-attributes
      // https://stackoverflow.com/a/8708345/14144258
      var parentElement = $('<div class="form-row row al_split_date_parent">');
      
      var monthId = dateElement.id + '-month';
      var monthParent = $('<div class="col">');
      var monthLabel = $('<label>{{month}}</label>');
      monthLabel.attr( 'for', monthId );
      var monthElement = $('<select class="form-select al_split_date month ' + dateElement.id + '">');
      monthElement.attr( 'id', monthId );
      monthElement.attr( 'name', monthId );
      
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
      dayElement.attr( 'name', dayId );
      
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
      yearElement.attr( 'name', yearId );
      
      var errorElement = $('<div id="' + dateElement.id + '-error" class="da-has-error al_split_date_error"></div>');
        
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
      // TODO bug: In codepen, this isn't getting validated for 'required'
      // until 'submit'. Maybe it's different in da.
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
      // Required even being present makes it true
      if (is_required(monthElement)) {{
        monthElement.attr( 'required', 'true' );
        monthElement.prop( 'required', 'true' );
        dayElement.attr( 'required', 'true' );
        dayElement.prop( 'required', 'true' );
        yearElement.attr( 'required', 'true' );
        yearElement.prop( 'required', 'true' );
      }}
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
        var val = data.month + '/' + data.day + '/' + data.year;
        if ( val === '//' ) {{
          val = '';
        }}
        $(dateElement).val( val );
      }};  // Ends updateDate()
      
      // -- Validation for these elements --
        
      // Store dev-created messages 
      var almin = $(dateElement).data('almin');
      var almax = $(dateElement).data('almax');
      var almin_message = $(dateElement).data('alminmessage');
      var almax_message = $(dateElement).data('almaxmessage');
      // TODO: invalid date message. Allow dev to disable?
      // TODO: 4-digit year message. Allow dev to disable?
      
      // TODO: I think it might be possible to use `groups`, but
      // I'm not sure how. This plugin is poorly documented.
      
      // `depends` docs: https://stackoverflow.com/a/13626251/14144258 and
      // https://jqueryvalidation.org/validate/
      // TODO: the most recent error message overwrites the others. Maybe
      // help? https://stackoverflow.com/a/71957334. Alternatively, in validation
      // method, put data on nodes and first check for other data that has
      // already been put in there about prioritization level.
      $('.' + dateElement.id).each(function(index, elem) {{
        $(elem).rules( 'add', {{
          // 'required' should be happening correctly automatically
          _alvaliddate: true,  // Values must create an existing date (i.e. no 2/31)
          _al4digityear: true,
          almin: {{
            depends: function(element) {{
              return get_date_element_data({{element, attr: 'almin'}}) !== undefined;
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
              return get_date_element_data({{element, attr: 'almax'}}) !== undefined;
            }}
          }},
        }});  // ends add rules
        
        // TODO: Avoid later elements overwriting priority messages of earlier elements by
        // adding messages dynamically. Maybe https://stackoverflow.com/a/20928765/14144258
        // Maybe do it by adding data attribs in `addMethod()` and, in the same place
        // comparing one's own priority to that already present on the element/parent.
        
        // `.one()` will make sure this is only set once
        // TODO: bug with validation not working after an unrelated field gets invalid
        // input. Try `on` instead of `one`.
        // $(elem).on('addValidations', function (event) {{
          // console.log('$this', $(this));
          
          // [switching from hide to remove fixed it] √ TODO: too many days in month will show up if year is not 4-digit year and also something else? Maybe only after day number is too high? Also, stacks with others. Year style doesn't get "hidden". Refresh needed?
          // TODO: When leave empty field, field is highlighted even though there's no message and even when the date is not required. These aren't going through `errorPlacement`. `required` is always true. Why? It's a bool attrib and it's not present on the non-required fields.
          // Codepen quirk: Regular/default jQuery validation (for attribs like `min`)
          // don't seem to go through our `errorPlacement()`, but bug only happens if
          // click in and out of a non-required field after it's been highlighted
          // (note that it happens without a message) and then click in and out of
          // a required field that does then get a message underneath its individual
          // element.
          
          // TODO: bug: `errorPlacement` seems to not be called on submit, just on other
          // kinds of validation. wtf, jquery validation plugin.
        
          // Add this error validation to the existing error validation
          var originalErrorPlacement = $('#daform').validate().settings.errorPlacement;
          var errorPlacement = function(error, element) {{
            console.log('----')
            console.log('place error');
            // console.log(element);
            // Finds an AL date parent
            var $parent = get_$parent(element);
            
            // If this isn't an AL date, use the original behavior
            if (!$parent[0]) {{
              // console.log('not date part');
              originalErrorPlacement(error, element);
              return;
            }}
            
            // TODO: once one invalid field is valid, other fields that are invalid don't show
            // the message of their own invalidation.
            // Must preserve all messages and show them in order of priority somehow
            // TODO: For individual invalid fields, hide lower priority validation highlighting?
            
            // data-priority on element. Give that priority to the new error message.
            // show the error message with the highest priority of all the error messages.
            // See if error messages just accumulate if you let them, or if there's only
            // ever one per field. Also only highlight the most priority invalid field,
            // but do something different if the whole date is invalid? (lowest priority)
            
            // TODO next: How to keep old error messages and show them when
            // other error messages go away? `.hide()` ended up not hiding
            // some elements - not defining their `style` properly.
            
            // Do with CSS instead
            // // Otherwise, use our custom error labeling
            // // Hide all existing labels, so they don't pile up
            // // TODO: Hide or remove completely?
            // hide($( $parent.find('span.invalid-feedback') ));
            // // For codepen practice:
            // hide($( $parent.find('label.error') ));
            // // console.log('appending to $parent:', $parent);
            
            $(error).appendTo($parent.find('.al_split_date_error')[0]);
            show_only_last_error(element);
            
            // Add class 'is-invalid', set aria-invalid to true
            // and aria-describedby to something like
            // "dGVzdF8zX3BhcnQ-year-error dGVzdF8zX3BhcnQ-month-error dGVzdF8zX3BhcnQ-day-error"
            // https://stackoverflow.com/a/53404898/14144258
            // using the three elements' `id`s.
            // TODO: In future, this should depend on what kind of invalidation
            // it is. That info could be stored in a `data` attribute
          }};  // Ends errorPlacement()
          // Override the previous errorPlacement
          var validator = $("#daform").data('validator');
          validator.settings.errorPlacement = errorPlacement;
          
          // TODO next: How do we
          // show the error message for an invalid date (day) when the filed is
          // a month without higlighting the month? Returning valid for the month
          // will avoid highlighting it, but then won't show the error message.
          // I just don't know if we can handle higlights globally this way and
          // still have the behavior we need.
          // Old: If day is too high, clicking in and out of other
          // fields will highlight them too, even if they're valid. Is that
          // because of our global `highlight()`? Do we still want to sometimes
          // highlight them? E.g. when they have their own errors?
          
          // var originalHighlight = $('#daform').validate().settings.highlight;
          // var highlight = function(element, errorClass, validClass) {{
          //   // // Make sure this at least highlights the element itself
          //   // // console.log('highlight', $(element));
          //   // if ($(element).hasClass('al_split_date')) {{
          //   //   $(element).addClass('al_invalid');
          //   // }}
          //   originalHighlight(element, errorClass, validClass);
          // }};
          // // Override the previous highlight
          // var validator = $("#daform").data('validator');
          // validator.settings.highlight = highlight;
          // // console.log($('#daform').validate());  // log settings
          
          var originalUnhighlight = $('#daform').validate().settings.unhighlight;
          var unhighlight = function(element, errorClass, validClass) {{
            // Make sure this at least unhighlights the element itself
            if ($(element).hasClass('al_split_date')) {{
              
              // Remove label as that has stopped working automatically. It would be
              // better to know why the label isn't being removed in the first place.
              // How to track down?
              let $parent = get_$parent(element);
              let $error_container = $( $parent.find('.al_split_date_error')[0] );
              let $label = $( $error_container.find(`label[for="${{ $(element).attr('name') }}"`)[0] );
              $label.remove();
              show_only_last_error(element);
              
              // da has stopped the plugin from managing the 'error' class
              // and I believe we've found `is-invalid` to be inconsistent for
              // our uses.
              $(element).removeClass('al_invalid');
              // Ensure parent is valid if there are no errors left
              if ($error_container.text() === '') {{
                $parent.removeClass('al_invalid');
                $parent.removeClass('al_invalid_child');
              }}
              
            }}  // ends if is a split date
            originalUnhighlight(element, errorClass, validClass);
          }};
          // Override the previous highlight
          var validator = $("#daform").data('validator');
          validator.settings.unhighlight = unhighlight;
          
          // -- Messages --
          
          // IMPORTANT NOTE: If the developer can put in their own messages,
          // they will also be able to make sure that they are translated.
          // TODO: Can we make a template for these messages instead of putting
          // them in here?
          
          var default_min_message = 'This date is too early.';
          var default_max_message = 'This date is too late.';
          // Birthdays have a different default max message
          if (is_birthdate(elem)) {{
            default_max_message = 'The birthdate must be in the past.';
          }}
          
          var min_message = get_date_element_data({{
            element: this,
            attr: 'alminmessage'
          }}) || default_min_message;
          var max_message = get_date_element_data({{
            element: this,
            attr: 'almaxmessage'
          }}) || default_max_message;
          
          // Dynamically set the message
          // TODO: Do we need to ensure other messages aren't errased?
          // So far we've seen other messages still show up just fine.
          $(this).rules('add', {{
            
            /*
            Not able to replicate bug:
            1. Click in one date's field part
            1. Avoid entering any input
            1. Click in another date's field part
            1. Put something invalid into the field part
            1. Click out (into original field part or just to anywhere?)
            */
            
            messages: {{
              // TODO: For valid date, recommended is "The date must be a real date", but we
              // know it's the day that's the problem. Should we be more specific than the
              // recommendations?
              _alvaliddate: jQuery.validator.format('There are not that many days in this month.'),
              // _alvaliddate: function () {{
              //   // "monthname doesn't have that many days"
              // }},
              _al4digityear: 'The year must have 4 numbers.',
              almin: min_message,
              almax: max_message,
              // Will this be customizable with da `validation message:`?
              // Probably not. I don't know to fetch that message, though.
              // required: 'All fields are required',
            }},
          }});
          
        // }});  // ends on addValidations
        
        // Not sure if this custom event will be triggered late enough
        // in da to properly override what it needs to override.
        // The da stuff is happening before `daPageLoad`, so I'm not
        // sure why I was having trouble getting `.errorPlacement` to
        // work properly when it wasn't in `.on('change')`.
        $(elem).trigger('addValidations');
      }});  // ends for all 3 part dates
      
      // TODO: Add a message for an incomplete date only when the parent loses
      // focus? Not sure how.
      
    }});  // ends for each input
  
  // No jQuery validation for original field, since it doesn't work on hidden
  // elements last time we tried
  
  // --- Validation methods ---
  // Handling all fields' classes inside each validation needs to be
  // debugged. I think we need to do that to show the right
  // highlighting.
  
  /*
  When find a single invalid field
    Make all other fields' css valid-looking
    in errorPlacement: Hide old error messages and mark them as aria-hidden
    Show field as invalid
    Give parent class al_invalid_child
    Show field's invalidation message
  When find whole date invalid (min/max)
    Show one message
    Highlight all
  When find a field is valid
    Show previous invalid message
    Avoid unhighlighting other invalid fields
  When all individual fields are valid
    Remove class al_invalid_chlid? Maybe that class isn't necessary
    Unhighlight all fields (including removing parent class)
  */
  
  /* TODO: 'required' bug/problem:
  One of the month options is a blank option.
  That should count as not having a value, but it doesn't, so the
  'required' invalidation doesn't get triggered.
  */
  
  // - Inidividual field validations
  
  $.validator.addMethod('_al4digityear', function(value, element, params) {{
    /** Returns true if year input has 4 digits.
    *   Ensure invalid field is highlighted.
    *   Only day inputs can create mismatching dates. */
    let $year = $(get_$parent(element).find('.year')[0]);
    // Empty year is not invalid in this way
    if ($year.val() === '') {{return true;}}
    let is_valid = $year.val().length === 4 ;
    
    if (!is_valid) {{
      handle_part_validation({{
        element: $year[0],
        is_valid: is_valid,
      }});
    }}
    
    return is_valid;
  }});  // ends validate '_al4digityear'
  
  
  $.validator.addMethod('_alvaliddate', function(value, element, params) {{
    /** Returns false if full input values cannot be converted to a matching Date object.
    *   E.g. 2/43/2000 has an invalid day. HTML doesn't do this natively.
    *   Only day inputs can create mismatching dates.
    *   Ensure invalid field (day field) is highlighted.
    */
    let validity_vals = get_date_inputs_validity(element);
    
    let is_day_valid = validity_vals.day === true;
    // Display invalid highlighting on day elem if needed
    if (!is_day_valid) {{
      let $al_parent = get_$parent(element);
      let day_elem = $al_parent.find('.day')[0];
      handle_part_validation({{
        element: day_elem,
        is_valid: is_day_valid,
      }});
    }}
    
    // For this particular invalidation, avoid highlighting anything
    // other than the day element
    let is_valid = true;
    if ($(element).hasClass('day')) {{
      is_valid = is_day_valid;
    }}
    
    // TODO: But then how do we get the error message
    // to appear
    
    return is_valid;
  }});  // ends validate '_alvaliddate'
  
  
  // - Whole date validations
  
  $.validator.addMethod('almin', function(value, element, params) {{
    /** Returns true if full date is >= min date Also makes sure
    *   all fields get highlighted when invalid. */
    // TODO: need to figure out how to prioritize types of validation.
    
    var data = get_date_data(element);
    // Don't show an error if the date is only partly filled
    if (data.year == '' || data.month == '' || data.day === '') {{
      return true;
    }}
    var date_val = new Date(data.year + '-' + data.month + '-' + data.day);
    if ( isNaN( date_val ) ) {{
      return true;
    }}
    // TODO: Catch invalid `almin` attr values? Useful for devs. Otherwise very hard
    // for devs to track down. Log in console?
    var date_min = new Date(get_date_element_data({{element, attr: 'almin'}}));
    let is_valid = date_val >= date_min;
    handle_parent_validation({{ element, is_valid }});
    
    return is_valid;
  }});  // ends validate 'almin'
  
  
  $.validator.addMethod('almax', function(value, element, params) {{
    /** Returns true if full date is <= max date. Also makes sure
    *   all fields get highlighted when invalid. */
    
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
    
    var max_attr = get_date_element_data({{element, attr: 'almax'}});
    // TODO: Catch invalid almax values? Log in console?
    var date_max = new Date(max_attr);
    if ( isNaN(date_max) && is_birthdate(element)) {{
      date_max = new Date(Date.now())
    }}
    
    // Note that a year input of "1" counts as a date of 2001
    let is_valid = date_val <= date_max;
    handle_parent_validation({{ element, is_valid }});
    
    return is_valid;
  }});  // ends validate 'almax'
  
  
  // --- Getting from and manipulate the DOM ---
  
  
  function show_only_last_error(element) {{
    /** Shows only the last error in the error list that's in the error container. */
    let $parent = get_$parent(element);
    

    $parent.find('.al_split_date_error label:not(:last-child)').each(function (index, label) {{
      $(label).attr('hidden', 'true');
      $(label).attr('aria-hidden', 'true');
    }});
    $parent.find('.al_split_date_error label:last-child').each(function (index, label) {{
      $(label).removeAttr('hidden');
      $(label).attr('aria-hidden', 'false');
    }});
  }};  // Ends show_only_last_error()
  
  
  function get_date_data(element) {{
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
    *   Easier to maintain all in one place.
    * 
    * @param {{Node}} element AL split date element. */
    // `.closest()` will get the element itself if appropriate
    return $(element).closest('.al_split_date_parent');
  }};  // Ends get_$parent()
  
  
  function get_$date(element) {{
    let $date = $(get_$parent(element).closest('.dafieldpart').children('input'));
    return $date;
  }};  // Ends get_$date()
  
  
  function is_birthdate(element) {{
    /** If the element is part of a al birthdate field, returns true, otherwise false.
    * 
    * @params {{Node}} element A split date part.
    */
    let $search_results = get_$parent(element).parent().find('.daALBirthDateTestValidation');
    return Boolean($search_results[0]);
  }};  // Ends is_birthdate()
  
  
  function get_date_element_data({{element, attr}}) {{
    let $date = get_$date(element);
    return $date.data(attr);
  }};  // Ends get_date_element_data()
  
  
  function is_required(element) {{
    /*** Return true if date value is required, other wise return false.
    * 
    * @param {{Node}} element AL split date part.
    */
    let $date = get_$date(element);
    let is_required = $date.closest('.da-form-group').hasClass('darequired');
    // console.log(is_required, $date);
    return is_required;
  }}  // Ends is_required()
  
  
  // --- Validation class manipulation ---
  
  function hide($element) {{
    $element.attr('aria-hidden', 'true');
    $element.attr('hidden', 'true');
  }};
  
  
  function show($element) {{
    $element.attr('aria-hidden', 'false');
    $element.attr('hidden', 'false');
  }};
  
  
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
    // TODO: When multiple individual fields are invalid (e.g. empty when required), should
    // only the field that is currently in focus be highlighted as an error?
    var $element = $(element);
    var $al_parent = get_$parent(element);
    if (is_valid) {{
      $al_parent.removeClass('al_invalid_child');
      $element.removeClass('al_invalid');
    }} else {{
      handle_parent_validation({{element, is_valid: true}});
      $al_parent.addClass('al_invalid_child');
      // // Ensure just the field in focus is highlighted right now
      // $al_parent.find('.al_split_date').removeClass('al_invalid');
      $element.addClass('al_invalid');
    }}
  }};  // Ends handle_part_validation()
  
  
  // --- Validation calculations ---
  
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
    * @examples:
    * 10//2000  // {{year: true, month: true, day: true}}
    * 10/10/2000  // {{year: true, month: true, day: true}}
    * 10/32/2000  // {{year: true, month: true, day: false}}
    * Only day can be invalid in this way?
    * 12/42/2000  // {{year: true, month: true, day: false}}? {{year: false, month: true, day: false}}?
    * 
    * @returns {{year: bool, month: bool, day: bool}} Date parts that are
    *   valid will have a value of `true`
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
  function setDate({{year, month, date}}) {{
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
