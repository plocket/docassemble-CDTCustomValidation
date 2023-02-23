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
console.log('---- starting custom date 2');
// for codepen
//$('#daform').validate();

// This is an adaptation of Jonathan Pyle's datereplace.js


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
than that, but that's messy - detect valid on change, detect invalid on blur.

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
  // console.log( 'date_data in get_date_date()', date_data );
  return date_data;
}};  // Ends get_date_data()

  
function get_$date(element) {{
  // TODO: Try $(element).closest()...
  let $date = $(get_$parent(element).closest('.dafieldpart').children('input')[0]);
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
// === Validation options ===
// ==================================================
// ==================================================
  
function set_up_validation($al_parent) {{
  place_errors();
}};  // Ends set_up_validation()

  
function place_errors() {{
  // Add this error validation to the existing error validation
  var original_error_placement = $('#daform').validate().settings.errorPlacement;
  var error_placement = function(error, element) {{
    
    var $al_parent = get_$parent(element);
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
  var validator = $("#daform").data('validator');
  validator.settings.errorPlacement = error_placement;
}};  // Ends place_errors()
  
  
// ==================================================
// ==================================================
// === Validation methods ===
// ==================================================
// ==================================================
  
  
}} catch (error) {{
  console.error('Error in AL date CusotmDataTypes', error);
}}



// ====================================
// ====================================
// ====================================
// for codepen
//$(document).trigger('daPageLoad');

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


class ALBirthDateTestValidation2(ALThreePartsDateTestValidation2):
    name = "ALBirthDateTestValidation2"
    input_type = "ALBirthDateTestValidation2"
    javascript = js_text.format(
        month=word("Month"), day=word("Day"), year=word("Year")
    ).replace("ALThreePartsDateTestValidation2", "ALBirthDateTestValidation2")
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
