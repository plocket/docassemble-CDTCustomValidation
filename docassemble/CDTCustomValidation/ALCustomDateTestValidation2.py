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
// $('#daform').validate({{ errorClass: 'is-invalid' }});  // for codepen (no custom required message)
//$('#daform').validate({{ errorClass: 'is-invalid', messages: {{curbs: {{ required: 'bar' }}}} }});  // for codepen

console.log('---- starting custom date 2');

// This is an adaptation of Jonathan Pyle's datereplace.js

/*
* Notes to keep around:
* - Don't include a min date default for birthdays. Too hard to predict developer needs, like great-grandmother's birthday. Document that developers need to set a min value if they want one.
* - Rule names must avoid dashes.
* - year input of "1" counts as a date of 2001 and "11" is 2011
* - I didn't find anything like `defaultShowErrors` for other functions, here or in da
* - left to right precedence
*
* Validation priority (https://design-system.service.gov.uk/components/date-input/#error-messages):
*  1. missing or incomplete information (when parent is no longer in focus, highlight fields missing info?)
*  2. information that cannot be correct (for example, the number ‘13’ in the month field)
*     (TODO: maybe less than 4 digits in year counts? Maybe it's #3 priority?)
*  3. information that fails validation for another reason
*
* For invalidation styling see al_dates.css.
*/

/*
TODO: prioritize validation

DONE:
  - BUG: `required` da custom message doesn't show up, field isn't highlighted
  - Put `aria-describedby` on field somewhere somehow
  - Change var name "element" to "field" where possible
  - Handle un-required partial dates on submission (was already done in our da customdatatype)
  - Provide attrib for default message that will appear before
      our defaults if no more specific message is given.
  - [Answer: We do want to require a 4-digit year] Discuss requiring a 4-digit year
  - MVP highlight full element and none of the individual elements (with exclamation)
  - (Bug) When one field is invalid, manipulating other fields will
      affect errors on the first field invalidations, hiding them
      and unhighlighting that first field when the other field is
      valid and other stuff. This includes manipulating other non-date
      fields. `showErrors` doesn't allow detecting element when things
      are valid, so how do manage that?
      When the other field is invalid already, triggering its invalidation
      message will hide the first field's message, but it won't remove
      the highlighting.
  - Bug:
    click to year
    Enter somethihng
    set Day to 35
    click out
    fix day
    all errors disappear
*/

// da doesn't log the full error sometimes, so we'll do our own try/catch
try {{

$(document).on('daPageLoad', function(){{
  $('input[type="ALThreePartsDateTestValidation2"]').each(function(){{
    let $al_date = replace_date(this);
    set_up_validation($al_date);
  }});  // ends for each date datatype
}});  // ends on da page load
  
  
function replace_date(original_date) {{
  /** Replace the original date element with our 3 fields and
  *   make sure the fields update the original date value.
  * 
  * @param {{HTML Node}} date The original date element.
  * 
  * @returns {{jQuery obj}} AL container for all the split date elements
  */
  let $original_date = $(original_date);
  $original_date.hide();
  $original_date.attr('type', 'hidden');
  $original_date.attr('aria-hidden', 'true');
      
  // -- Construct the input components --
      
  let date_id = $original_date.attr('id');
  let $year = create_date_part({{date_id, type: 'year'}});
  let $month = create_month(date_id);
  let $day = create_date_part({{date_id, type: 'day'}});
  
  var $al_date = $('<div class="al_split_date form-row row">');
  $original_date.before($al_date);
  
  $al_date.append($month.closest('.col'));
  $al_date.append($day.closest('.col'));
  $al_date.append($year.closest('.col'));
  
  // Avoid .data() for our dynamic stuff - caching problems
  // https://forum.jquery.com/topic/jquery-data-caching-of-data-attributes
  // https://stackoverflow.com/a/8708345/14144258
  if (is_required($al_date)) {{
    $year.attr('required', true);
    $month.attr('required', true);
    $day.attr('required', true);
  }}
  
  use_previous_values({{$original_date, $al_date}});
  
  // Ensure original date field is updated when needed so that
  // submitting the form sends the right data.
  // Updates will be triggered when the user leaves an input field
  $year.on('change', update);
  $month.on('change', update);
  $day.on('change', update);
  function update() {{
    update_original_date($al_date);
  }};
  
  add_error_container($al_date);
  
  return $al_date;
}};  // Ends replace_date()
  
  
// TODO: Move `set_up_validation` to here? Closer to where it's called.
  

// A shame these have to be split into month and others
function create_date_part({{type, date_id}}) {{
  /** Return one date part with a label and input inside a container.
  *   TODO: Should we use `name` instead of `id`? Will that mess up `aria-describedby`?
  * 
  * @param {{str}} type 'year' or 'day'
  * @param {{str}} date_id ID of the original date field
  * 
  * @returns undefined
  */
  var $col = $('<div class="col col-3 col-' + type + '">');
  var id = date_id + '_' + type;
  // '_ignore' prevents the field from being submitted, avoiding a da error
  // TODO: Should id be the same as name? Would that mess up `aria-describedby`?
  let name =  '_ignore_' + id;
  
  var $label = $('<label>{{' + type + '}}</label>');
  $label.attr( 'for', name );
  $col.append($label);
  
  // `inputmode` ("numeric") not fully supported yet (02/09/2023). When it is,
  // change to `type='text'`. Also, when remove `type='number'` also add a check
  // when in invalid day check to see if either the year or day is not a number.
  // See warning in that function.
  // Reconsider type `number`, but avoid attr `pattern` - 
  // voice control will enter invalid input (https://github.com/alphagov/govuk-design-system-backlog/issues/42#issuecomment-775103437)
  
  // aria-describedby is ok to have, even when the date-part error is
  // not present or is display: none
  var $field = $('<input class="form-control al_field ' + type + ' ' + date_id + '" type="number" min="1" inputmode="numeric">');
  $field.attr('id', id);
  $field.attr('name', name);
  // There's only one message element, so all fields are described by it
  // I think jquery validation plugin uses the error message's `for` attrib,
  // but I'm not sure where that originally comes from. Looks like the original
  // input's `id`, but I'm not sure why the plugin is using that.
  $field.attr('aria-describedby', id + '-error');
  $col.append($field);
  
  return $field;
}};  // Ends create_date_part()

  
function create_month(date_id) {{
  /** Return one month type date part given the original date node id.
  *   TODO: Should we use `name` instead of `id`? Will that mess up `aria-describedby`?
  * 
  * @param {{str}} date_id ID of the original date field
  * 
  * @returns undefined
  */
  var $col = $('<div class="col col-month">');
  
  let id = date_id + '_month';
  // '_ignore' prevents the field from being submitted, avoiding a da error
  // TODO: Should id be the same as name? Would that mess up `aria-describedby`?
  let name =  '_ignore_' + id;
  
  let $label = $('<label>{{month}}</label>');
  $label.attr( 'for', name );
  $col.append($label);
  
  // TODO: Add aria-describedby if necessary (check da)
  // aria-describedby is ok to have, even when the date-part error is
  // not present or is display: none
  // `for` is label of field
  // `aria-describedby` is supplemental info
  // https://developer.mozilla.org/en-US/docs/Web/CSS/display#display_none
  // https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Attributes/aria-hidden
  var $field = $('<select class="form-select al_field month ' + date_id + '">');  // unique
  $field.attr('id', id);
  $field.attr('name', name);
  // There's only one message element, so all fields are described by it
  $field.attr('aria-describedby', id + '-error');
  add_months($field);  // unique
  
  $col.append($field);
  
  return $field;
}};  // Ends create_month()
  
  
function add_months(select) {{
  /** Add month values to selection field.
  * 
  * @param {{HTML Node | $ obj}} select A <select> node.
  * 
  * @returns undefined
  */
  
  let $select = $(select);
  
  // "No month selected" option
  let $blank_opt = $('<option value=""></option>');
  $select.append( $blank_opt );
  
  // Add every calendar month (based on user's computer's date system? lanugage?)
  for(let month=0; month < 12; month++) {{
    let $opt = $('<option>');
    if ( month < 9 ) {{
      $opt.val('0' + (month + 1));
    }} else {{
      $opt.val(month + 1);
    }}

    // Convert the month number to a month name for the option text
    let date = new Date(1970, month, 1);
    $opt.text(date.toLocaleString('default', {{ month: 'long' }}));

    $select.append($opt);
  }}  // ends for every month
}};  // End add_months()
  
  
function use_previous_values({{$original_date, $al_date}}) {{
  /** If $original_date has an existing value, set the date fields values to match.
  *   E.g. If we're returning to a variable that has already been defined.
  * 
  * @param {{$ obj}} $original_date jQuery obj of the original date element.
  * @param {{$ obj}} $al_date jQuery obj of the al parent of our split date parts.
  * 
  * @returns undefined
  */
  if ($original_date.val()) {{
    let full_date = new Date($original_date.val());
    
    $($al_date.find('input.year')[0]).val(`${{full_date.getFullYear()}}`);
    
    let month = `${{full_date.getMonth() + 1}}`;
    if (month.length === 1) {{
      month = `0${{month}}`;
    }}
    let $month = $($al_date.find('select.month')[0]);
    $($month.children('option[value="' + month + '"]')).prop('selected', true);
    
    $($al_date.find('input.day')[0]).val(`${{full_date.getDate()}}`);
  }}  // ends if original date has val
}};  // Ends use_previous_values()
  
  
function add_error_container($al_date) {{
  /** Add element that will contain all errors.
  * 
  * @param {{$ obj}} $al_date The al parent of our split date parts.
  * 
  * @returns undefined
  */
  let $original_date = get_$original_date($al_date);
  let $error = $('<div id="al_' + $original_date.attr('id') + '_error" class="da-has-error al_error"></div>');
  $al_date.append($error);
  return $error;
}};  // Ends add_error_container()
  

// Update value of original input when values change.
function update_original_date($al_date) {{
  /** Update value in original date field using the values
  *   of the al split date parts.
  * 
  * @param {{$ obj}} $original_date The original date element.
  * @param {{$ obj}} $al_date The al parent of our split date parts.
  * 
  * @returns undefined
  */
  var data = get_date_data($al_date);
  var val = data.month + '/' + data.day + '/' + data.year;
  if ( val === '//' ) {{
    val = '';
  }}
  get_$original_date($al_date).val( val );
}};  // Ends updateDate()
  
  
// ==================================================
// ==================================================
// === Get elements and element data ===
// ==================================================
// ==================================================

function is_required(element) {{
  /*** Returns true if date value is required, otherwise returns false.
  * 
  * @param {{Node}} element AL split date element. Can be parent of date parts.
  * 
  * @returns {{bool}}
  */
  let $original_date = get_$original_date(element);
  return $original_date.closest('.da-form-group').hasClass('darequired');
}}  // Ends is_required()
  
  
function get_date_data(element) {{
  /**
  * Given an element that holds a part of the date information,
  * return the full date data as an object.
  * 
  * @param {{HTML Node | $ obj}} element Any al split date element, including parent.
  * 
  * @returns {{year: str, month: str, day: str}}
  */
  var year_elem = get_$al_date(element).find('input.year')[0];
  var month_elem = get_$al_date(element).find('select.month')[0];
  var day_elem = get_$al_date(element).find('input.day')[0];
  var date_data = {{
    year: $(year_elem).val(),
    month: $(month_elem).val(),
    day: $(day_elem).val(),
  }};
  return date_data;
}};  // Ends get_date_data()
  
  
function is_birthdate(element) {{
  /** If the element is part of a al birthdate field, returns true, otherwise false.
  * 
  * @param {{HTML Node}} element Any al split date element, including al parent.
  * @returns {{bool}}
  */
  let birthdate = get_$al_date(element).parent().find('.daALBirthDateTestValidation2')[0];
  return Boolean(birthdate);
}};  // Ends is_birthdate()

  
function get_$original_date(element) {{
  /** Returns jQuery obj of original date element.
  * 
  * @param {{HTML Node}} element Any al split date element, including al parent.
  * 
  * @returns {{jQuery obj}}
  */
  return $($(element).closest('.dafieldpart').children('input')[0]);
}};  // Ends get_$original_date()
  
  
function get_$al_date(element) {{
  /** Return the element we created to surround our date elements.
  *   Easier to maintain all in one place.
  * 
  * @param {{HTML Node}} element Any element.
  * 
  * @returns {{jQuery obj}} Note: can be an "empty" jQuery object.
  */
  // `.closest()` will get the element itself if appropriate
  return $(element).closest('.al_split_date');
}};  // Ends get_$al_date()
  
  
// ==================================================
// ==================================================
// === Validation ===
// ==================================================
// ==================================================
  
function set_up_validation($al_date) {{
  /** Uses jQuery validation plugin to set up validation functionality
  * 
  * @param {{$ obj}} $al_date jQuery obj of the al parent of our split date parts.
  * 
  * @returns undefined
  */
  let validator = $("#daform").data('validator');
  set_up_errorPlacement(validator);
  set_up_highlight(validator);
  set_up_unhighlight(validator);
  
  $al_date.find('.al_field').each(function make_validator_options (index, field) {{
    add_rules(field);
    add_messages(field);
    add_to_groups(field);
  }});
}};  // Ends set_up_validation()

  
function set_up_errorPlacement(validator) {{
  /** Sometimes override existing errorPlacement.
  * 
  * TODO: Pass in validator?
  * 
  * @returns undefined
  */
  let original_error_placement = validator.settings.errorPlacement;
  validator.settings.errorPlacement = function al_errorPlacement(error, field) {{
    /** Put all errors in one spot at the bottom of the parent.
    *   Only runs once per field.
    */
    let $al_date = get_$al_date(field);
    // If this isn't an AL date, use the original behavior
    if (!$al_date[0] && original_error_placement !== undefined) {{
      original_error_placement(error, field);
      return;
    }}

    $(error).appendTo($al_date.find('.al_error')[0]);
  }};  // Ends al_errorPlacement()
  
}};  // Ends set_up_errorPlacement()
  
function set_up_highlight(validator) {{
  /** For our date elements, override pre-existing highlight method.
  * 
  * @returns undefined
  */
  let original_highlight = validator.settings.highlight;
  validator.settings.highlight = function al_highlight(field, errorClass, validClass) {{
    /** Highlight parent instead of individual fields. MVP  */
    let $al_date = get_$al_date(field);
    // If this isn't an AL date, use the original behavior
    if (!$al_date[0] && original_highlight !== undefined) {{
      original_highlight(field, errorClass, validClass);
      return;
    }}
    
    $al_date.addClass('al_invalid');
    // Avoid highlighting individual elements
    $al_date.find('.al_field').each(function(index, field) {{
      $(field).removeClass('is-invalid');  // Just a Bootstrap class
    }});
    
  }};  // Ends al_highlight()
}};  // Ends set_up_highlight()
  
function set_up_unhighlight(validator) {{
  /** For our date elements, override pre-existing highlight method.
  * 
  * @returns undefined
  */
  let original_unhighlight = validator.settings.unhighlight;
  validator.settings.unhighlight = function al_unhighlight(field, errorClass, validClass) {{
    /** Unhighlight parent instead of individual fields. MVP  */
    let $al_date = get_$al_date(field);
    $al_date.removeClass('al_invalid');
    original_unhighlight(field, errorClass, validClass);
  }};  // Ends al_unhighlight()
}};  // Ends set_up_unhighlight()
  

function add_rules(field) {{
  /** Add all date rules to a given field.
  * 
  * @param {{HTML Node}} field An al split date field.
  * 
  * @returns undefined
  */
  let rules = {{
    // TODO: try returning value of 'day' to get a better error message.
    _alInvalidDay: true,  // e.g. 1/54/2000 is invalid` TODO: Should devs be able to disable this?
    _alInvalidYear: true,
    alMin: get_$original_date(field).attr('data-alMin') || false,
    // TODO: try:
    // alMax: is_birthdate(field) || get_$original_date(field).attr('data-alMax'),
    alMax: {{
      depends: function(field) {{
        // Birthdates always have a max value
        // TODO: Should the dev still be able to override?
        if ( is_birthdate(field) ) {{
          return true;
        }}
        // Otherwise, check the field itself
        return get_$original_date(field).attr('data-alMax') !== undefined;
      }}
    }},
  }};  // ends rules
  
  $(field).rules('add', rules);
}};  // Ends add_rules()
  
  
function add_messages(field) {{
  /** Adds custom messages that don't need parameters
  * 
  * @param {{HTML Node}} field An al split date field.
  * 
  * @returns undefined
  */
  let messages = $("#daform").data('validator').settings.messages;
  let name = get_$original_date(field).attr('name');
  // If the original date field has custom messages
  if (messages[name] !== undefined) {{
    // Add the `required` custom message. `undefined` is fine.
    $(field).rules('add', {{
      messages: {{
        required: messages[get_$original_date(field).attr('name')].required,
      }}
    }});  // ends add rules
  }}  // ends if required message exists
}};  // Ends add_messages()
  
  
function add_to_groups(field) {{
  /** Add field to its group dynamically after-the-fact. We have
  *   to do this because da has already created its groups and we
  *   don't want to override anything.
  *   Note: Adding groups dynamically here won't be reflected in `validator.settings`
  * 
  *   Inspired by https://stackoverflow.com/a/9688284/14144258
  * 
  * @param {{HTML Node}} field An al split date field.
  * 
  * @returns undefined
  */
  let groups = $("#daform").data('validator').groups;
  groups[ $(field).attr('name') ] = get_$original_date(field).attr('id');
}};  // Ends add_to_groups()
  
  
// ==================================================
// ==================================================
// === Validation methods ===
// ==================================================
// ==================================================
  
// -- Whole date validations --

$.validator.addMethod('alMin', function(value, field, params) {{
  /** Returns true if full date is >= min date or incomplete. */
  if (!date_is_ready_for_min_max(field)) {{
    return true;
  }}
  
  // Avoid usinig `params`, which could be in many different formats.
  // Just get date data from the actual fields
  var data = get_date_data(field);
  // TODO: Catch invalid `data-alMin` attr values? Useful for devs.
  // Otherwise very hard for devs to track down. Log in console?
  // Non-MVP. Make an issue.
  var date_min = new Date( get_$original_date(field).attr('data-alMin') );
  var date_val = new Date(data.year + '-' + data.month + '-' + data.day);
  
  return date_val >= date_min;
  
}}, function alMinMessage (validity, field) {{
  /** Returns the string of the invalidation message. */
  return (
    get_$original_date(field).attr('data-alMinMessage')
    || get_$original_date(field).attr('data-alDefaultMessage')
    || `The date needs to be on or after ${{ get_$original_date(field).attr('data-alMin') }}.`
  );
}});  // ends validate 'alMin'
  
  
$.validator.addMethod('alMax', function(value, field, params) {{
  /** Returns true if full date is <= max date or is incomplete. */
  if (!date_is_ready_for_min_max(field)) {{
    return true;
  }}

  // Avoid usinig `params`, which could be in many different formats.
  // Just get date data from the actual fields
  var data = get_date_data(field);

  // TODO: Catch invalid alMax attr values? Log in console?
  var max_attr = get_$original_date(field).attr('data-alMax');
  var date_max = new Date(max_attr);
  if ( isNaN(date_max) && is_birthdate(field)) {{
    date_max = new Date(Date.now());
  }}

  var date_val = new Date(data.year + '-' + data.month + '-' + data.day);
  
  return date_val <= date_max;
  
}}, function alMaxMessage (validity, field) {{
  /** Returns the string of the invalidation message. */
  
  var default_MaxMessage = `The date needs to be on or before ${{ get_$original_date(field).attr('data-alMax') }}.`;
  // Birthdays have a different default max message
  if (!get_$original_date(field).attr('data-alMax') && is_birthdate(field)) {{
    default_MaxMessage = 'A <strong>birthdate</strong> must be in the past.';
  }}
  
  return (
    get_$original_date(field).attr('data-alMaxMessage')
    || get_$original_date(field).attr('data-alDefaultMessage')
    || default_MaxMessage
  );
}});  // ends validate 'alMax'
  
  
// --- Validate individual fields ---
// Always validate each individual field any time any fields are changed.
  
$.validator.addMethod('_alInvalidDay', function(value, field, params) {{
  /** Returns false if full input values cannot be converted to a
  *   matching Date object. E.g. 12/32/2000 will be converted to 1/1/2001.
  *   HTML doesn't do this check itself.
  *   Right now only day inputs can create mismatching dates.
  *   
  *   Note: We need to validate each field for this. If they put Jan 30 and
  *   then change month to Feb, we need to show the error then.
  */
  // Only validate day for this, but still validate it any time any of
  // the split date parts are checked.
  // Doesn't need to be abstracted anymore in some ways, but it does
  // make this `addMethod` section of the code cleaner.
  return has_valid_day(field);
}}, function alInvalidDayMessage (validity, field) {{
  /** Returns the string of the invalidation message. */
  
  // Always return a custom message first
  let custom_msg = get_$original_date(field).attr('data-alInvalidDayMessage')
                   || get_$original_date(field).attr('data-alDefaultMessage');
  if (custom_msg) {{
    return custom_msg;
  }}
  
  let input_date = get_$al_date(field).find('.day').val();
  
  // If the date is only partly filled, we can't give a useful message
  // without a heck of  a lot of work, so give a generalized invalid day
  // default message. Other is a stretch goal.
  let data = get_date_data(field);
  if (data.year == '' || data.month == '') {{
    return `No month has ${{input_date}} days.`;
  }}
  
  // Otherwise we can give the full default message
  let input_year = get_$al_date(field).find('.year').val();
  let converted_year = (new Date(`1/1/${{input_year}}`)).getFullYear();
  let input_month = get_$al_date(field).find('.month option:selected').text();
  
  return `${{input_month}} ${{converted_year}} doesn't have ${{input_date}} days.`;
}});  // ends validate '_alInvalidDay'
  

$.validator.addMethod('_alInvalidYear', function(value, field, params) {{
  /** Returns true if year is empty or has 4 digits. */
  
  // Check year to make sure it's 4 digits
  let text = get_$al_date(field).find('input.year')[0].value;
  // Empty year is not invalid in this way
  if (text.length === 0) {{return true;}}
  // Dates will remove leading 0's, thus sadly 0011 == 2011
  if (text.length !== 4 || text[0] === '0') {{
    return false;
  }} else {{
    return true;
  }}
  
}}, function alInvalidYearMessage (validity, field) {{
  /** Returns the string of the invalidation message. */
  return (
    get_$original_date(field).attr('data-alInvalidYearMessage')
    || get_$original_date(field).attr('data-alDefaultMessage')
    || `The year needs to be 4 digits long and cannot start with "0".`
  );
}});  // ends validate '_alInvalidYear'
  
  
// ==================================================
// ==================================================
// === Calculations ===
// ==================================================
// ==================================================

function date_is_ready_for_min_max(element) {{
  /** Return true if date input is ready to be evaluated for min/max
  *   date value invalidation.
  * 
  * @param {{HTML Node}} element Any al split date element, including the parent.
  * 
  * @returns {{bool}}
  */
  var data = get_date_data(element);
  // Don't evaluate min/max if the date is only partly filled
  if (data.year == '' || data.month == '' || data.day === '') {{
    return false;
  }}
  // Not sure how we'd get here, but don't evaluate min/max if the date is
  // invalid in some other way. Maybe negative numbers?
  var date_val = new Date(data.year + '-' + data.month + '-' + data.day);
  if (isNaN(date_val)) {{
    return false;
  }}
  
  // Don't need to avoid an invalid day situation. Seems to work
  // without that check in here.
  
  return true;
}};  // Ends date_is_not_ready_for_min_max()
  

function has_valid_day(element) {{
  /** Given a date part element, returns true if:
  *   - the day is <= 31 and year or month is empty
  *   - all fields are filled and the day date is <= max days in the given month
  *   Returns false if either:
  *   - The day date is > 31 or
  *   - The day date is > the' max days in the given month
  * 
  * Inspired by https://github.com/uswds/uswds/blob/728ba785f0c186e231a81865b0d347f38e091f96/packages/usa-date-picker/src/index.js#L735
  * 
  * @param element {{HTML Node}} Any element in the al split date picker
  * 
  * @returns bool True if day date is valid
  * 
  * @examples:
  * 10//2000  // true
  * 10/10/2000  // true
  * 12/42/2000  // false
  */
  var data = get_date_data(element);
  if (parseInt(data.day) > 31) {{
    return false;
  }}
  // Don't invalidate if the date is only partly filled. Empty input fields
  // get handled other places.
  if (data.year === '' || data.month === '' || data.day === '') {{
    return true;
  }}

  const dateStringParts = [data.year, data.month, data.day];
  const [year, month, day] = dateStringParts.map((str) => {{
    let value;
    const parsed = parseInt(str, 10);
    if (!Number.isNaN(parsed)) value = parsed;
    return value;
  }});
  
  // WARNING: If we change the `type` of the year or day
  // to be 'text', we need to check return false if any
  // dateStringParts part === null

  const checkDate = setDate({{
    year: year,
    month: month - 1,
    date: day
  }});

  // 12/32/2000 would have transformed into 1/1/2001
  if (
    checkDate.getFullYear() !== year ||
    checkDate.getMonth() !== (month - 1) ||
    checkDate.getDate() !== day
  ) {{
    return false;
  }}

  return true;
}};  // Ends has_valid_day()

  
function setDate({{year, month, date}}) {{
  /**
  * Set date from month day year
  *
  * @param {{number}} year the year to set
  * @param {{number}} month the month to set (zero-indexed)
  * @param {{number}} date the date to set
  * 
  * @returns {{Date}} the set date
  */
  const newDate = new Date(0);
  newDate.setFullYear(year, month, date);
  return newDate;
}};


// ====================================
// ====================================
// ====================================
// for codepen
//$(document).trigger('daPageLoad');
  
  
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


class ALThreePartsDateTestValidation2(CustomDataType):
    name = "ALThreePartsDateTestValidation2"
    input_type = "ALThreePartsDateTestValidation2"
    # Alternatively, is it possible to allow the developer to put in their own values
    # for these labels?
    javascript = js_text.format(month=word("Month"), day=word("Day"), year=word("Year"))
    jq_message = word("Answer with a valid date")
    is_object = True
    mako_parameters = [
      'min', 'max',  # not yet appropriate to use
      'alMin', 'alMinMessage', 'alMax', 'alMaxMessage',
      'alInvalidDayMessage', 'alInvalidYearMessage', 'alDefaultMessage'
    ]

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


class ALBirthDateTestValidation2(ALThreePartsDateTestValidation2):
    name = "ALBirthDateTestValidation2"
    input_type = "ALBirthDateTestValidation2"
    javascript = js_text.format(
        month=word("Month"), day=word("Day"), year=word("Year")
    ).replace("ALThreePartsDateTestValidation2", "ALBirthDateTestValidation2")
    jq_message = word("Answer with a valid date of birth")
    is_object = True
    mako_parameters = [
      'min', 'max',  # not yet appropriate to use
      'alMin', 'alMinMessage', 'alMax', 'alMaxMessage',
      'alInvalidDayMessage', 'alInvalidYearMessage', 'alDefaultMessage'
    ]

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
