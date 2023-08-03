/*
Dropdown menu must have id of the input id + "-dropdown-menu"
Element parameter is either the input box or an array
  If array, element 0 = text for the filter, element 1 = dropdown container id
Options in dropdown menu must have id of the input id + "-option"
*/

function filterSearchBar(element) { // SOURCE: https://www.w3schools.com/howto/howto_js_filter_dropdown.asp
    var filter, a, i;
    if (element instanceof Array) {
      filter = element[0].toUpperCase();
      dropdown_container = document.getElementById(element[1]);
      dropdown_container.style = "display:flex;";
    } else {
      filter = element.value.toUpperCase();
      dropdown_container = document.getElementById(element.id + "-dropdown-menu");
    }
    a = dropdown_container.getElementsByTagName("a");
    for (i = 0; i < a.length; i++) {
      txtValue = a[i].textContent || a[i].innerText;
    if (txtValue.toUpperCase().indexOf(filter) > -1) {
      a[i].style.display = "";
    } else {
      a[i].style.display = "none";
    }
  }
  }
  
  function selectSearchBar(element, text) {
  if (searching) {
    var search_box = document.getElementsByName(searching_section)[0];
    curr_text = search_box.value;
    search_box.value = curr_text.slice(0, searching_index + 1) + "[" + text + "]" + curr_text.slice(end_of_search_index);
    search_box.focus();
    search_box.selectionStart = searching_index + text.length + 3;
    search_box.selectionEnd = search_box.selectionStart;
    endPageSearch(search_box, null, false);
  } else {
    var search_box = document.getElementById(element.id.replace('-option',''))
    search_box.value = text;
  }
  }
  
  function resizeTextArea(element) {
    //element.style.height = 0;
    element.style.height = (element.scrollHeight) + 2 + "px";
  }
  
  function insertHTML(element, id, section = true) {
    var type = element.innerText;
    if (section) { // if for a section
      section = document.getElementsByName(String(id))[0]; // use section being edited
    } else {
  
    }
    var first_insert = "*["; // default to bold
    var last_insert = "]*";
    var ref_page = false;
  
    if (type == 'i') { // italics
        first_insert = "/[";
        last_insert = "]/";
    } else if (type == '*') { // new unordered list
        first_insert = "\n-[\n*";
        last_insert = '\n]-\n';
    } else if (type == '1)') { // new ordered list
      first_insert = "\n=[\n*";
      last_insert = '\n]=\n';
    } else if (type == '>') { // tab
        first_insert = ">";
        last_insert = '';
    } else if (type == '@') { // reference page
        ref_page = true;
        if (section.selectionStart == section.selectionEnd) {
          first_insert = '@';
          last_insert = '';
        } else {
          first_insert = "@[";
          last_insert = "]";
        }
    }
  
    var text = String(section.value);
    var start = section.selectionStart; // SOURCE: https://ourcodeworld.com/articles/read/282/how-to-get-the-current-cursor-position-and-selection-within-a-text-input-or-textarea-in-javascript
    var end = section.selectionEnd;
    var length = section.value.length;
    text = text.slice(0, start) + first_insert + text.slice(start, end) + last_insert + text.slice(end + 1, length); // SOURCE: https://stackoverflow.com/questions/4313841/insert-a-string-at-a-specific-index
    section.value = text;
    section.focus({preventScroll: true}); // SOURCE: https://stackoverflow.com/questions/34968174/set-text-cursor-position-in-a-textarea
    // fixme: the above line of code causes the page to scroll up 
  
    if (end - start <= 0) { // fix for no text
        new_index = end + first_insert.length;
        section.selectionStart = new_index;
        section.selectionEnd = new_index;
    }
    resizeTextArea(element);
  
  
    if (ref_page) {
        pageSearch(section);
    }
  
    return;
  }
  
  let searching = false;
  let searching_index = null;
  let end_of_search_index = null;
  let searching_section = null;
  let last_key = null;
  let curr_focus = null;
  function pageSearch(textbox, e = null) {
    var switch_on = false;
    var arrow_down = false;
    var arrow_up = false;
  
    if (!e) {
        switch_on = true;
    } else if (e.key == '@' || last_key == 'Shift' && e.key == '2') {
        switch_on = true;
    } else if (e.key == 'ArrowDown') {
      arrow_down = true;
    } else if (e.key == 'ArrowUp') {
      arrow_up = true;
    }
  
    if (switch_on) {
        searching = true;
        searching_index = textbox.selectionStart - 1;
        searching_section = textbox.name;
    }
  
    if (searching) {
  
        dropdown = document.getElementById(textbox.name + '-dropdown-menu');
  
        if (textbox.selectionStart < searching_index + 1 || textbox.value.slice(searching_index,searching_index + 1) != '@') {
            endPageSearch(textbox.parentElement);
            return;
        }
  
        //sections = document.getElementById('sections');
        end_of_search_index = textbox.selectionStart;
        filterSearchBar([textbox.value.slice(searching_index + 1, textbox.selectionStart), textbox.name + '-dropdown-menu'])
  
        // handlers for navigating through the dropdown options
        if (arrow_down) {
          if (curr_focus == null) {
            curr_focus = document.getElementById(textbox.name + '-dropdown-menu').firstElementChild;
            curr_focus.focus();
          } else if (curr_focus.nextElementSibling != null) {
            curr_focus = curr_focus.nextElementSibling;
            curr_focus.focus();
          }
        } else if (arrow_up) {
          if (curr_focus != null) {
            if (curr_focus.previousElementSibling == null) {
              curr_focus = null;
              textbox.focus();
            } else {
              curr_focus = curr_focus.previousElementSibling;
              curr_focus.focus();
            }
          }
        }
  
    } else {
  
        last_key = e.key; // storing to reference shift + 2 for the @ symbol
  
    }
  
    return;
  }
  
  function endPageSearch(container, event = null, is_container=true) {
  if (event) { // if focusout occured on a child, ignore
    if ((event.currentTarget.contains(event.relatedTarget))) { // SOURCE: https://stackoverflow.com/questions/12092261/prevent-firing-the-blur-event-if-any-one-of-its-children-receives-focus
      return;
    }
  }
  var textbox_id;
  if (is_container) {
    textbox_id = container.id.replace('_container','');
  } else {
    textbox_id = container.name;
  }
  var dropdown = document.getElementById(textbox_id + '-dropdown-menu'); // fixme
  searching = false;
  searching_index = null;
  searching_section = null;
  curr_focus = null;
  end_of_search_index = null;
  dropdown.style = "display:none;";
  return;
  }
  