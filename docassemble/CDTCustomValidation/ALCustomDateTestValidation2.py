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
//$('#daform').validate();  // for codepen

console.log('---- starting custom date 2');

// This is an adaptation of Jonathan Pyle's datereplace.js

/*
Notes:
- Rule names must have no dashes.
- year input of "1" counts as a date of 2001 and "11" is 2011
*/

/* Validation priority (https://design-system.service.gov.uk/components/date-input/#error-messages):
*  1. missing or incomplete information (when parent is no longer in focus, highlight fields missing info?)
*  2. information that cannot be correct (for example, the number ‘13’ in the month field)
*     (TODO: maybe less than 4 digits in year counts? Maybe it's #3 priority?)
*  3. information that fails validation for another reason
*
* For invalidation styling see al_dates.css.
*/

/* Validation pseudocode

for any field on any change? on blur? both? Should be more complicated
than that, but that's messy - first time detect invalid on blur then on change; or
possibly detect valid on change, detect invalid on blur.

  if required (should take care of itself) (ideally only after parent has lost focus)
    if any field is empty
      unhighlight other fields/"all fields" higlighting
      highlight empty fields
      show message
  
  if !4 digit year (ideally not while editing year field)
    unhighlight "all fields" highlighting
    keep other individual highlighting?
    highlight year
    show message

  if min
    if no other errors
      if all fields are filled in
        if below min
          highlight all fields
          show message
  if max
    same
*/

/*
TODO: prioritize validation
TODO: Handle un-required partial dates
TODO: Provide attrib for default message that will appear before
      our defaults if no more specific message is given.
TODO: Discuss requiring a 4-digit year
*/

// da doesn't log the full error sometimes, so we'll do our own try/catch
try {{

$(document).on('daPageLoad', function(){{
  
  $('input[type="ALThreePartsDateTestValidation2"]').each(function(){{
    do_everything(this);
  }});  // ends for each date datatype
  
}});  // ends on da page load

  
function do_everything(element) {{
  let $date = $(element);
  let {{$al_parent, $year, $month, $day, $error}} = replace_date($date);
  set_up_validation($al_parent);
}};
  
function replace_date($date) {{
  /** Replace the original date element with our 3 fields and
  *   make sure the fields update the original date value. */
  $date.hide();
  $date.attr('type', 'hidden');
  $date.attr('aria-hidden', 'true');
      
  // -- Construct the input components --
      
  // Avoid .data() for our dynamic stuff - caching problems
  // https://forum.jquery.com/topic/jquery-data-caching-of-data-attributes
  // https://stackoverflow.com/a/8708345/14144258
  var $al_parent = $('<div class="form-row row al_split_date_parent">');
  $date.before($al_parent);
  
  let date_id = $date.attr('id');
  let $year = create_date_part({{date_id, type: 'year'}});
  let $month = create_month(date_id);
  let $day = create_date_part({{date_id, type: 'day'}});
  
  if (is_required($al_parent)) {{
    $year.attr('required', true);
    $month.attr('required', true);
    $day.attr('required', true);
  }}
  
  $al_parent.append($month.closest('.col'));
  $al_parent.append($day.closest('.col'));
  $al_parent.append($year.closest('.col'));
  
  use_previous_values({{$date, $al_parent}});
  
  // Ensure original date field is updated when needed so that
  // submitting the form sends the right data.
  // Updates will be triggered when the user leaves an input field
  $year.on('change', update);
  $month.on('change', update);
  $day.on('change', update);
  function update() {{
    update_original_date({{$date, $al_parent}});
  }};
  
  let $error = add_error($al_parent);
  
  return {{$al_parent, $year, $month, $day, $error}};
}};  // Ends replace_date()
  

// A shame these have to be split into month and others
function create_date_part({{type, date_id}}) {{
  /** Return one date part with a label and input inside a container.
  * 
  * @param {{str}} type 'year' or 'day'
  * @param {{str}} date_id ID of the original date field
  */
  var $col = $('<div class="col">');
  var id = date_id + '_' + type;
  
  var $label = $('<label>{{' + type + '}}</label>');
  $label.attr( 'for', id );
  $col.append($label);
  
  // `inputmode` ("numeric") not fully supported yet (02/09/2023). When it is, remove type number
  // Reconsider type `number`, but avoid attr `pattern` - 
  // voice control will enter invalid input (https://github.com/alphagov/govuk-design-system-backlog/issues/42#issuecomment-775103437)
  var $field = $('<input class="form-control al_split_date ' + type + ' ' + date_id + '" type="number" min="1" inputmode="numeric">');
  $field.attr( 'id', id );
  // '_ignore' prevents the field from being submitted and causing an error
  // TODO: Should id be the same?
  $field.attr( 'name', '_ignore_' + id );
  $col.append($field);
  
  return $field;
}};  // Ends create_date_part()

  
function create_month(date_id) {{
  /** Return one month type date part.
  * 
  * @param {{str}} date_id ID of the original date field
  */
  var $col = $('<div class="col">');
  
  var id = date_id + '_month';
  var $label = $('<label>{{month}}</label>');
  $label.attr( 'for', id );
  $col.append($label);
  
  var $field = $('<select class="form-select al_split_date month ' + date_id + '">');  // unique
  $field.attr( 'id', id );
  // '_ignore' prevents the field from being submitted and causing an error
  // TODO: Should id be the same?
  $field.attr( 'name', '_ignore_' + id );
  add_months($field);  // unique
  
  $col.append($field);
  
  return $field;
}};  // Ends create_month()
  
  
function add_months($select) {{
  /** Add month values to selection field. */
  
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
  
  
function use_previous_values({{$date, $al_parent}}) {{
  /** If $date has an existing value, set the date fields values to match.
  *   E.g. If we're returning to a variable that has already been defined. */
  if ($date.val()) {{
    let full_date = new Date($date.val());
    
    $($al_parent.find('input.year')[0]).val(`${{full_date.getFullYear()}}`);
    
    let month = `${{full_date.getMonth() + 1}}`;
    if (month.length === 1) {{
      month = `0${{month}}`;
    }}
    let $month = $($al_parent.find('select.month')[0]);
    $($month.children('option[value="' + month + '"]')).prop('selected', true);
    
    $($al_parent.find('input.day')[0]).val(`${{full_date.getDate()}}`);
  }}  // ends if original date has val
}};  // Ends use_previous_values()
  
  
function add_error($al_parent) {{
  /** Add element that will contain all errors. */
  let $date = get_$date($al_parent);
  let $error = $('<div id="al_' + $date.attr('id') + '_error" class="da-has-error al_split_date_error"></div>');
  $al_parent.append($error);
  return $error;
}};  // Ends add_error()
  

// Update value of original input when values change.
function update_original_date({{$date, $al_parent}}) {{
  var data = get_date_data($al_parent);
  var val = data.month + '/' + data.day + '/' + data.year;
  if ( val === '//' ) {{
    val = '';
  }}
  $date.val( val );
}};  // Ends updateDate()
  
  
// ==================================================
// ==================================================
// === Get elements and element data ===
// ==================================================
// ==================================================

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
  
  
function get_date_data($element) {{
  /**
  * Given an element that holds a part of the date information,
  * return the full date data as an object.
  * 
  * @returns {{year: str, month: str, day: str}}
  */
  var year_elem = get_$parent($element).find('input.year')[0];
  var month_elem = get_$parent($element).find('select.month')[0];
  var day_elem = get_$parent($element).find('input.day')[0];
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
  * @params {{Node}} element A split date part.
  */
  let birthdate = get_$parent(element).parent().find('.daALBirthDateTestValidation2')[0];
  return Boolean(birthdate);
}};  // Ends is_birthdate()

  
function get_$date(element) {{
  let $date = $($(element).closest('.dafieldpart').children('input')[0]);
  return $date;
}};  // Ends get_$date()
  
  
function get_$parent(element) {{
  /** Return the element we created to surround our date elements.
  *   Easier to maintain all in one place.
  * 
  * @param {{Node}} element AL split date element. */
  // `.closest()` will get the element itself if appropriate
  return $(element).closest('.al_split_date_parent');
}};  // Ends get_$parent()
  
  
  
  
// ==================================================
// ==================================================
// === Validation ===
// ==================================================
// ==================================================
  
function set_up_validation($al_parent) {{
  place_errors();
  $al_parent.find('.al_split_date').each(function (index, element) {{
    add_rules(element);
    add_messages(element);
  }});
}};  // Ends set_up_validation()

  
function place_errors() {{
  // Add this error validation to the existing error validation
  let original_error_placement = $('#daform').validate().settings.errorPlacement;
  let error_placement = function(error, element) {{
    
    let $al_parent = get_$parent(element);
    // If this isn't an AL date, use the original behavior
    if (!$al_parent[0]) {{
      // console.log('not date part');
      original_error_placement(error, element);
      return;
    }}

    $(error).appendTo($al_parent.find('.al_split_date_error')[0]);
    // TODO: Remove `aria-describedby` when field is valid
    $(element).attr('aria-describedby', error.id);
    // show_only_last_error(element);  // Hopefully won't need this
  }};  // Ends error_placement()
  
  // Override the previous errorPlacement
  let validator = $("#daform").data('validator');
  validator.settings.errorPlacement = error_placement;
}};  // Ends place_errors()
  

function add_rules(element) {{
  /** Add all date rules to a given element.
  * 
  * @param {{HTML Node}} element A date part node. */
  let rules = {{
    // TODO: try returning value of 'day' for crossing bounds to get a better
    // error message.
    _alcrossingbounds: true,  // e.g. 1/54/2000 is invalid` TODO: Should devs be able to disable this?
    almin: {{
      depends: function(element) {{
        return get_$date(element).attr('data-almin') !== undefined;
        // TODO: try below to get better message about being too early or too late
        //return get_$date(element).attr('data-almin') || false;
      }}
    }},
    almax: {{
      depends: function(element) {{
        // Birthdates always have a max value
        // TODO: Should the dev still be able to override? 
        if ( is_birthdate(element) ) {{
          return true;
        }}
        // Otherwise, check the element itself
        return get_$date(element).attr('data-almax') !== undefined;
      }}
    }},
  }};  // ends rules
  
  $(element).rules('add', rules);
}};  // Ends add_rules()
  
  
function add_messages(element) {{
  /** Add all messages for rules for a given element.
  * 
  * @param {{HTML Node}} element A date part node. */
  
  var default_max_message = 'This date is too late.';
  // Birthdays have a different default max message
  if (is_birthdate(element)) {{
    default_max_message = 'A <strong>birthdate</strong> must be in the past.';
  }}
  
  let $elem = get_$date(element);
  let messages = {{
    // Note: Cannot be functions
    messages: {{
      _alcrossingbounds: $elem.attr('data-alcrossingboundsmessage') || $elem.attr('data-aldefaultmessage') || 'There are not that many days in the month.',
      almin: $elem.attr('data-alminmessage') || $elem.attr('data-aldefaultmessage') || 'This date is too early.',
      almax: $elem.attr('data-almaxmessage') || $elem.attr('data-aldefaultmessage') || 'This date is too late.',
    }},
  }};  // ends rules
  $(element).rules('add', messages);
}};  // Ends add_messages()
  
  
// ==================================================
// ==================================================
// === Validation methods ===
// ==================================================
// ==================================================
  
// -- Whole date validations --

$.validator.addMethod('almin', function(value, element, params) {{
  /** Returns true if full date is >= min date Also makes sure
  *   all fields get highlighted when invalid. */
  if (!date_is_ready_for_min_max(element)) {{
    return true;
  }}
  
  var data = get_date_data(element);
  var date_val = new Date(data.year + '-' + data.month + '-' + data.day);
  // TODO: Catch invalid `data-almin` attr values? Useful for devs.
  // Otherwise very hard for devs to track down. Log in console?
  var date_min = new Date( get_$date(element).attr('data-almin') );
  let is_valid = date_val >= date_min;
  // handle_parent_validation({{ element, is_valid }});
  
  return is_valid;
}});  // ends validate 'almin'
  
  
$.validator.addMethod('almax', function(value, element, params) {{
  /** Returns true if full date is <= max date. Also makes sure
  *   all fields get highlighted when invalid. */
  if (!date_is_ready_for_min_max(element)) {{
    return true;
  }}

  var data = get_date_data(element);
  var date_val = new Date(data.year + '-' + data.month + '-' + data.day);
  if (isNaN(date_val)) {{
    return true;
  }}

  // TODO: Catch invalid almax attr values? Log in console?
  var max_attr = get_$date(element).attr('data-almax');
  var date_max = new Date(max_attr);
  if ( isNaN(date_max) && is_birthdate(element)) {{
    date_max = new Date(Date.now());
  }}
  let is_valid = date_val <= date_max;
  // handle_parent_validation({{ element, is_valid }});

  return is_valid;
}});  // ends validate 'almax'
  
  
// TODO: Is this an individual field validation or a whole-field validation?
$.validator.addMethod('_alcrossingbounds', function(value, element, params) {{
  /** Returns false if full input values cannot be converted to a
  *   matching Date object. E.g. 12/32/2000 will be converted to 1/1/2001.
  *   HTML doesn't do this check itself.
  *   Right now only day inputs can create mismatching dates.
  * 
  *   Ensure invalid field (day field) is highlighted.
  */
  let validity_vals = which_inputs_dont_cross_bounds(element);

  let day_is_valid = validity_vals.day === true;
  // Display invalid highlighting on day elem if needed
  if (!day_is_valid) {{
    let $al_parent = get_$parent(element);
    let day_elem = $al_parent.find('.day')[0];
    // handle_part_validation({{
    //   element: day_elem,
    //   is_valid: day_is_valid,
    // }});
  }}

  // For this particular invalidation, avoid highlighting anything
  // other than the day element
  let is_valid = true;
  if ($(element).hasClass('day')) {{
    is_valid = day_is_valid;
  }}

  // TODO: How do we get the error message to appear after another
  // field is marked as valid? Keep the error around and reveal it?
  return is_valid;
}});  // ends validate '_alcrossingbounds'
  
  
// ==================================================
// ==================================================
// === Calculations ===
// ==================================================
// ==================================================

function date_is_ready_for_min_max(element) {{
  /** Return true if date input is ready to be evaluated for min/max
  *   date value invalidation.
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
  
  // // TODO: Don't show this error if the input values don't create
  // // the expected date (e.g. date is 45th of Jan)
  // let validity_vals = which_inputs_dont_cross_bounds(element);
  // if (validity_vals.day === false) {{
  //   return false;
  // }}
  
  return true;
}};  // Ends date_is_not_ready_for_min_max()
  

// TODO: get rid of double negatives
function which_inputs_dont_cross_bounds(element) {{
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
}};  // Ends which_inputs_dont_cross_bounds()

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
    mako_parameters = ['almin', 'almax', 'alminmessage', 'almaxmessage', 'alcrossingboundsmessage', 'aldefaultmessage']

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
    mako_parameters = ['almin', 'almax', 'alminmessage', 'almaxmessage', 'alcrossingboundsmessage', 'aldefaultmessage']

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
