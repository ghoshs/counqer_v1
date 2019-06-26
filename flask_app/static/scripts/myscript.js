var subentities = document.getElementById('subentities');
var subject = document.getElementById('subject');
var subjectIDlist = {};
var subjectID = '';

var objentities = document.getElementById('objentities');
var object = document.getElementById('object');
var objectIDlist = {};
var objectID = '';

var predentities = document.getElementById('predentities');
var predicate = document.getElementById('predicate');
var predicateIDlist = {};
var predicateID = '';

var option='wikidata';
var predrequest = new XMLHttpRequest();

// url to the data directory which has the wikidata/wd_predicates.json and dbpedia/dbp_predicates.json files
// SimpleHTTPServer invoked in localhost on demo directory
var localpath ='http://127.0.0.1:5000/static/';
var flaskurl = 'http://localhost:5000/spoquery'; 

/** server edits**/
// var localpath ='https://counqer.mpi-inf.mpg.de/static/';
// var flaskurl = 'https://counqer.mpi-inf.mpg.de/spoquery'; 

// function to process the jsonp (json padding) function returned by the json files and
// populate the predicate options
function jsonCallback (result){
  var jsonOptions = result[option];
  Object.keys(jsonOptions).forEach(function(itemtype) {
    jsonOptions[itemtype].forEach(function(item) {
      if (!(item in predicateIDlist)) {
        var dropdown_option = document.createElement('option');
        dropdown_option.value = item;
        predentities.appendChild(dropdown_option);
        predicateIDlist[item] = {value: item, type: itemtype};
      }
    });
  });
  // console.log('in jsoncallback, result: ',result);
  // console.log($("#predentities").children().length);
}

// function for displaying information messages
function displayinfo(message) {
  $('#displayalert').children().replaceWith(message);
}

// function to refresh results
function result_refresh () {
  // results
  $(".first").hide();
  $("#s1").empty();
  $("#p1").empty();
  $("#o1").empty();
  $(".second > tbody").empty();
  $(".second > thead > tr > td").empty();
  $(".second").hide();
  // $(".second").html('<strong>Related Predicates</strong><hr>');
}

// function to refresh inputs
function form_refresh () {
  $('#objentities').empty();
  $('#subentities').empty();
  $('#predentities').empty();
  $('#subject').val('');
  $('#predicate').val('');
  $('#object').val('');
  $("#subject").prop('disabled', false);
  $("#object").prop('disabled', false);
  subjectIDlist = {};
  predicateIDlist = {};
  objectIDlist = {};
  subjectID = '';
  predicateID = '';
  objectID = '';

  // if ($('#predentities').children().length == 0) {
  //   if (option === 'wikidata') {

  //   }
  // }
  var msg = "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'>We are waiting for your input.</div>";
  displayinfo(msg);
}

// function to initiate ajax for loading predicate options 
$.fn.predautocomplete = function () {
  var fname, path;
  // console.log('option in predautocomp:::'+option);
  if (option === 'wikidata') {
    fname = 'wd_predicates.json';
  }
  else {
    fname = 'dbp_predicates.json';
  }
  path = localpath + 'data/' + option + '/' + fname;
  $.ajax({
    type: 'GET',
    url : path,
    dataType: 'jsonp'
  });
};

// function to read returned triples
function gettriples(response) {
  var result = [];
  var len = response.length;
  var i;
  if ('o1Label' in response[0] || 's1Label' in response[0]) {
    i = 1;
  }
  else {
    i = 0;
  }
  for (; i<len; i++) {
    var temp = {};
    for (item in response[i]){
      if (item === 's2Label'){
        temp['s2'] = join_entities(response[i][item]);
      }
      else if (item === 'o2Label') {
        temp['o2'] = join_entities(response[i][item]);
      }
      else {
        temp[item] = response[i][item];
      }
    }
    result.push(temp);
  }
  return result;
}

// add results to related predicates
function add_child (s2, p2, o2) {
  // console.log('add child ', s2, o2);
  if ($(".second").is(":hidden")) {
    $(".second").show();
  }
  // text = '<div class="row vertical-align">' +
  //         '<div class="col btn s2">' + s2 + '</div>'+
  //         '<div class="col btn btn-warning p2">' + p2 + '</div>' +
  //         '<div class="col btn o2">' + o2 + '</div>'+
  //         '</div>';
  // $(".second").append(text);
  text = '<tr>' +
         '<td class="s2 partial">' + insert_trunc_and_full_result(s2) + '</td>' +
         '<td> <div class="col-12 btn btn-warning p2">' + p2 + '</div></td>' +
         '<td class="o2 partial">' + insert_trunc_and_full_result(o2) + '</td>' +
         '</tr>';
  $(".second > tbody").append(text);
  // console.log(text);
}

// join string array to comma separated string with total entity count
function join_entities(entityarray){
  var entities = [], entityLabel=[];
  var len = entityarray.length;
  var result = {'trunc': '', 'full': ''}, overflow_idx = -1, overflow_limit = 15;
  var link_prefix = '<a href="', link_mid='" target="_blank">', link_suffix='</a>';
  for (var i=0; i<len; i++){
    var item = '', itemlabel = '';
    item = entityarray[i].split('/');
    itemlabel = item[item.length - 1].split('_').join(' ');
    entityLabel.push(itemlabel);
    
    // insert href for entities
    if (entityarray[i].indexOf('dbpedia') != -1){
      item = link_prefix + entityarray[i] + link_mid;
    }
    else if (entityarray[i].indexOf('wikidata') != -1) {
      item = link_prefix + item.slice(0, item.length - 1).join('/') + link_mid;
    }
    // literals have no href
    else {
      item = '';
    }
    // console.log(item);
    entities.push(item);
    
    if (overflow_idx < 0 && overflow_limit > 0){
      overflow_limit -= itemlabel.length;
      if (overflow_limit <= 0){
        overflow_idx = i;
      }
    }
  }
  // reset overflow limit
  overflow_limit = 15;
  if (overflow_idx >= 0){
    for (var i=0; i<= overflow_idx; i++){
      var end_idx = entityLabel[i].length;
      if (end_idx >= overflow_limit){
        end_idx = overflow_limit;
      }
      if (entities[i].length > 0){
        result['trunc'] += entities[i] + entityLabel[i].slice(0, end_idx+1) + link_suffix;
      }
      else {
        result['trunc'] += entityLabel[i].slice(0, end_idx+1);
      }
      overflow_limit -= end_idx;
      if (i < entities.length - 1){
        result['trunc'] += '; '
      }
    }
    // result = entities.slice(0,overflow_idx+1).join('; ')
    // result = result.slice(0,overflow_limit+1);
    result['trunc'] = result['trunc'] + ' ... (' + (entities.length).toString() + ' in total)';
  }
  // else {
  for (var i=0; i<=entities.length-1; i++){
    if (entities[i].length > 0){
      result['full'] += entities[i] + entityLabel[i] + link_suffix;
    }
    else {
      result['full'] += entityLabel[i];
    }
    if (i < entities.length - 1){
      result['full'] += '; '
    }
  } 
  // }
  if (result['trunc'].length == 0) {
    result['trunc'] = result['full'];
  }
  // For empty results
  if (result['full'].length == 0) {
    result['full'] = '-';
    result['trunc'] = '-';
  }
  
  // console.log(entityarray.length);
  // console.log(result);
  return(result);
}

// function to add <p> elements for full and truncated results
function insert_trunc_and_full_result (entity) {
  // console.log('entity: ', entity);
  return ('<p class="truncresult">' + entity['trunc'] + '</p> <p class="fullresult">' + entity['full'] +'</p>');
}

// funtion to populate table after getting results
function displayresponse (results) {
  var triple1={'s1': {}, 'p1': '', 'o1': {}};
  var triple2={'direct': [], 'inverse': []};
  console.log(results);
  if ('error' in results) {
    if (results.error === 'No co-occurring pair'){
      var msg = "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong> We could not retrieve any related results!</div>";
      displayinfo(msg);
    }
  }
  triple1['p1'] = results.p1;
  var link_prefix_wd = '<a href="http://wikidata.org/entity/', link_prefix_dbp='<a href="http://dbpedia.org/resource/';
  var link_mid='" target="_blank">', link_suffix='</a>';
  // if initial query was <s, p, ?o>
  if ('s1' in results) {
    if (option === 'wikidata'){
      triple1['s1']['trunc'] = Object.keys(subjectIDlist).find(key => subjectIDlist[key] === results.s1);
      triple1['s1']['trunc'] = link_prefix_wd + results.s1 + link_mid + triple1['s1']['trunc'] + link_suffix;
    }
    else {
      var temp = results.s1.split('/');
      triple1['s1']['trunc'] =  temp[temp.length - 1].split('_').join(' ');
      triple1['s1']['trunc'] = link_prefix_dbp + results.s1 + link_mid + triple1['s1']['trunc'] + link_suffix;
    }
    triple1['s1']['full'] = triple1['s1']['trunc'];
  }
  // if initial query was <?s, p, o>
  if ('o1' in results) {
    if (option === 'wikidata') {
      triple1['o1']['trunc'] = Object.keys(objectIDlist).find(key => objectIDlist[key] === results.o1);
      triple1['o1']['trunc'] = link_prefix_wd + results.o1 + link_mid + triple1['o1']['trunc'] + link_suffix;
    }
    else {
      var temp = results.o1.split('/');
      triple1['o1']['trunc'] = temp[temp.length - 1].split('_').join(' ');
      triple1['o1']['trunc'] = link_prefix_dbp + results.o1 + link_mid + triple1['o1']['trunc'] + link_suffix;
    }
    triple1['o1']['full'] = triple1['o1']['trunc'];
  }
  if ('error' in results['response'] && 'error' in results['response_inv']) {
    var msg = "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong> We could not retrieve any results!</div>";
    displayinfo(msg);
  }
  else if ('error' in results['response_inv']) {
    if ('o1Label' in results['response'][0]) {
      triple1['o1'] = join_entities(results['response'][0]['o1Label']);
      triple1['type'] = 'direct';
    }
    if ('s1Label' in results['response'][0]) {
      triple1['s1'] = join_entities(results['response'][0]['s1Label']);
      triple1['type'] = 'direct';
    }
    triple2['direct'] = gettriples(results['response']);
  }
  else if ('error' in results['response']) {
    if ('o1Label' in results['response_inv'][0]) {
      triple1['o1'] = join_entities(results['response_inv'][0]['o1Label']);
      triple1['type'] = 'inverse';
    }
    if ('s1Label' in results['response_inv'][0]) {
      triple1['s1'] = join_entities(results['response_inv'][0]['s1Label']);
      triple1['type'] = 'inverse';
    }
    triple2['inverse'] = gettriples(results['response_inv']);
  }
  else {
    if ('o1Label' in results['response'][0]) {
      triple1['o1'] = join_entities(results['response'][0]['o1Label']);
      triple1['type'] = 'direct';
    }
    if ('s1Label' in results['response'][0]) {
      triple1['s1'] = join_entities(results['response'][0]['s1Label']);
      triple1['type'] = 'direct';
    }
    if ('o1Label' in results['response_inv'][0]) {
      triple1['o1'] = join_entities(results['response_inv'][0]['o1Label']);
      triple1['type'] = 'inverse';
    }
    if ('s1Label' in results['response_inv'][0]) {
      triple1['s1'] = join_entities(results['response_inv'][0]['s1Label']);
      triple1['type'] = 'inverse';
    }
    triple2['direct'] = gettriples(results['response']);
    triple2['inverse'] = gettriples(results['response_inv']);
  }
  // console.log(triple1);
  // console.log(triple2);
  // if (triple1.s1.length > 0 && triple1.p1.length > 0 && triple1.o1.length > 0){
  if (triple1.s1.hasOwnProperty('trunc') && triple1.p1.length > 0 && triple1.o1.hasOwnProperty('trunc')){  
    $(".first").show();
    if (triple1['type'] === "direct") {
      $("#s1").html(insert_trunc_and_full_result(triple1['s1']));
      $("#p1").html(triple1['p1']);
      $("#o1").html(insert_trunc_and_full_result(triple1['o1']));
    }
    else {
      $("#s1").html(insert_trunc_and_full_result(triple1['o1']));
      $("#p1").html(triple1['p1']);
      $("#o1").html(insert_trunc_and_full_result(triple1['s1']));
    }
    // console.log('s1.html: ', $("#s1").html());
    // console.log('p1.html: ', $("#p1").html());
    // console.log('o1.html: ', $("#o1").html());
  }
  else {
    if (triple2['direct'].length > 0 || triple2['inverse'].length > 0){
      var msg = "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong> We could not retrieve main results!! Please check the related results</div>";
      displayinfo(msg);
    }
  }
  if (triple2['direct'].length > 0){
    // Modify heading of related predicates
    if (results.get == 'enumE'){
      $(".second > thead > tr > td").empty().append('<strong> Related Enumerating Predicates </strong>');
    }
    else if (results.get == 'enumG'){
      $(".second > thead > tr > td").empty().append('<strong> Related Counting Predicates </strong>');
    }
    // Add row child for each related predicate SPO triple
    var len = triple2['direct'].length;
    // if (triple1['s1'].length > 0){
    if (triple1['s1'].hasOwnProperty('trunc')){
      for (var i=0; i<len; i++){
        // if ('s1' in results) {
        // add_child(triple1['s1'], triple2['direct'][i]['p2'], triple2['direct'][i]['o2']);
        // }
        // queried object is the subject for related predicates
        // else {
        //   add_child(triple1['s1'], triple2['direct'][i]['p2'], triple2['direct'][i]['o2']);
        // }
        // add related results 
        if ((results['get'] === 'enumG' && triple1['s1']['full'].indexOf(';') === -1) || (results['get'] === 'enumE')){
          add_child(triple1['s1'], triple2['direct'][i]['p2'], triple2['direct'][i]['o2']);
        }
      }
    }
  }
  if (triple2['inverse'].length > 0) {
    // Modify heading of related predicates
    if (results.get == 'enumE'){
      $(".second > thead > tr > td").empty().append('<strong> Related Enumerating Predicates </strong>');
    }
    else if (results.get == 'enumG'){
      $(".second > thead > tr > td").empty().append('<strong> Related Counting Predicates </strong>');
    }
    // Add row child for each related predicate SPO triple
    var len = triple2['inverse'].length;
    // if (triple1.s1.length > 0) {
    if (triple1.s1.hasOwnProperty('trunc')){
      for (var i=0; i<len; i++){
        if (results['get'] ===  'enumG') {
          if ('s1' in results && triple1['s1']['full'].indexOf(';') === -1) {
            // add inv results if s1 is a single entity
              // console.log(triple1.s1.full, triple1.s1.full.indexOf(';'));
              add_child(triple1['s1'], triple2['inverse'][i]['p2'], triple2['inverse'][i]['o2']);
          }
          // queried object is the subject for related predicates
          else if (triple1['o1']['full'].indexOf(';') === -1){
            // add inv results if o1 is a single entity
              // console.log('inv: ', triple1.o1.full, triple1.o1.full.indexOf(';'));
              add_child(triple1['o1'], triple2['inverse'][i]['p2'], triple2['inverse'][i]['o2']);
          }
        }
        if (results['get'] === 'enumE') {
          add_child(triple2['inverse'][i]['s2'], triple2['inverse'][i]['p2'], triple1['s1']);
        }
      }
    }
  }

}
 
// function to load autocomplete options for wikidata entities
$.fn.wdautocomplete = function (entities, IDlist, val) {
  $.ajax({
    type: 'GET',
    url: 'https://www.wikidata.org/w/api.php',
    dataType: 'jsonp',
    data: {
      'action': 'wbsearchentities',
      'search': val,
      'format': 'json',
      'language': 'en',
      'type': 'item'
    },
    success: function(result, status){
      var jsonOptions = result['search'];
      // refresh datalist options
      // if (jsonOptions.length > 0){
      //   entities.innerHTML = '';
      // }
      jsonOptions.forEach(function(item) {
        // create new dropdown items
        if (!(item['label'] in IDlist)){
          var dropdown_option = document.createElement('option');
          dropdown_option.value = item['label']+': ' + item['description'];
          entities.appendChild(dropdown_option);
          IDlist[item['label']] = item['id'];
        }
      });
      // console.log('after:: ',IDlist);
    },
    error: function(){
      subject.placeholder = "Couldn't load enity options :(";
    }
  });
  return;
}

// function to load autocomplete options for dbpedia entities
$.fn.dbpautocomplete = function (entities, IDlist, val) {
  $.ajax({
    type: 'GET',
    url: 'https://en.wikipedia.org/w/api.php',
    dataType: 'jsonp',
    data: {
      'action': 'opensearch',
      'search': val,
      'format': 'json',
      'language': 'en',
      'namespace': '0'
    },
    success: function(result, status){
      var jsonOptions = result[1];
      // refresh datalist options
      // if (jsonOptions.length > 0){
      //   entities.innerHTML = '';
      // }
      var urlList = result[result.length-1];
      i=0;
      jsonOptions.forEach(function(label) {
        if (!(label in IDlist)){
          var dropdown_option = document.createElement('option');
          dropdown_option.value = label;
          entities.appendChild(dropdown_option);
          IDlist[label] = urlList[i];
        }
        i=i+1;
      });
    },
    error: function(){
      subject.placeholder = "Couldn't load enity options :(";
    }
  });
  return;
}

// function to complaete sample queries
function samplequeries(payload){
  displayinfo(payload['waitmsg']);
  result_refresh();
  subjectIDlist[payload['subject']] = payload['subjectID'];
  $("#subject").val(payload['subject']);
  $("#predicate").val(payload['predicate']);
  $("#object").val(payload['object']);
  option = payload['kbname'];
  $.ajax({
    type: 'GET',
    url: flaskurl,
    contentType: 'application/json',
    dataType: 'json',
    data: {
      'option': payload['kbname'],
      'subject': payload['subjectID'],
      'predicate': payload['predicate'],
      'object': payload['object']
    },
    success: function(result, status){
      // console.log(result);
      // console.log(status);
      displayinfo(payload['endmsg']);
      displayresponse(result);
      // predicateIDlist = {};
      // $("#predicate").predautocomplete();
      subjectIDlist = {};
    },
    error: function(){
      console.log('error in flask get');
    }
  });
}

// ******************************** on document ready **************************************//
$(document).ready(function () {
  // ******************************** predicate events **************************************//
  // populate default predicate options (Wikidata) 
  $("#predicate").predautocomplete();
  // on active input in predicate box
  $("#predicate").on('input change', function () {
    // call for autocomplete options depending on KB option
    // set subject ID on proper matching input
    if ($(this).val() !== '' && $(this).val() in predicateIDlist) {
      predicateID = predicateIDlist[$(this).val()]["value"];
    }
    else {
      predicateID = '';
    }

    // check if predicate is enumerating
    if ($(this).val() !== '' && $(this).val() in predicateIDlist && predicateIDlist[$(this).val()]['type'] === 'enumG') {
      $("#object").val('Integer valued');
      $("#object").prop('disabled', true);
      if ($("#subject").attr("disabled")) {
        $("#subject").prop('disabled', false);
      }
    }
    else if ($("#object").attr("disabled") && $("#object").val() === 'Integer valued'){
      $("#object").val('');
      $("#object").prop('disabled', false); 
    }
  });
  // ******************************** subject events **************************************//
  // Empty dropdown content if no input is given
  $("#subject").blur(function () {
    if ($(this).val() === ''){
      $('#subentities').empty();
      subjectIDlist = {};
      subjectID = '';
    }
  });

  // on active input in subject box
  $("#subject").on('input change', function () {    
  // disable object if object input is non-empty
    var val = $(this).val();
    if (val !== '') {
      $("#object").prop('disabled', true);
      // call for autocomplete options depending on KB option
      // set subject ID on proper matching input
      if (val !== '' && option === 'wikidata') {
        if (val.split(':')[0] in subjectIDlist){
          subjectID = subjectIDlist[val.split(':')[0]];
        }
        else {
          $(this).wdautocomplete(subentities, subjectIDlist, val);
        }
      }
      else if (val !== '' && option === 'dbpedia'){
        if (val in subjectIDlist) {
          subjectID = subjectIDlist[$(this).val()];
          subjectID = subjectID.split('/');
          subjectID = subjectID[subjectID.length-1];
        }
        else {
          $(this).dbpautocomplete(subentities, subjectIDlist, val);
        }
      }
      else {
        subjectID = '';
      }
    }
    else {
     $("#object").prop('disabled', false); 
    }
    return;
  });
  // $("#subject").on('change', function () {
  //   subjectID = subjectIDlist[$(this).val().split(':')[0]];
  //   console.log('on change sub id: ', subjectID);
  // });
  // ******************************** object events **************************************//
  // Empty dropdown content if no input is given
  $("#object").blur(function () {
    if ($(this).val() === ''){
      $('#objentities').empty();
      objectIDlist = {};
    }
  });
  // on active input in object box
  $("#object").on('input change', function () {
    // disable subject if object input is non-empty
    var val = $(this).val();
    if (val !== '') {
      $("#subject").prop('disabled', true);
    }
    else {
     $("#subject").prop('disabled', false); 
    }

    // call for autocomplete options depending on KB option
    // set subject ID on proper matching input
    if (val !== '' && option === 'wikidata') {
      if (val.split(':')[0] in objectIDlist){
        objectID = objectIDlist[val.split(':')[0]];
      }
      else {
        $(this).wdautocomplete(objentities, objectIDlist, val);
      }
    }
    else if (val !== '' && option === 'dbpedia'){
      if (val in objectIDlist) {
        objectID = objectIDlist[val];
        objectID = objectID.split('/');
        objectID = objectID[objectID.length-1];
      }
      else {
        $(this).dbpautocomplete(objentities, objectIDlist, val);
      }
    }
    else {
      objectID = '';
    }
  });
  // ******************************** KB selection events **************************************//
  // changes made on selecting a KB preference
  $("#WD-btn").click(function () {
    if (option === 'dbpedia') {
      // refresh options when KB changes
      form_refresh();
    }
    option = 'wikidata';
    $("#WD-btn").addClass("btn-outline-infp").removeClass("btn-link");
    $("#DBP-btn").addClass("btn-link").removeClass("btn-outline-info");
    
    $("#predicate").predautocomplete();
  });
  $("#DBP-btn").click(function () {
    if (option === 'wikidata') {
      // refresh options when KB changes
      form_refresh();
    }
    option = 'dbpedia';
    $("#WD-btn").addClass("btn-link").removeClass("btn-outline-info");
    $("#DBP-btn").addClass("btn-outline-info").removeClass("btn-link");
    $("#predicate").predautocomplete();
  });
  // ******************************** form refresh events **************************************//
  $(".refresh").click(function () {
    option = 'wikidata';
    $("#WD-btn").addClass("btn-outline-infp").removeClass("btn-link");
    $("#DBP-btn").addClass("btn-link").removeClass("btn-outline-info");
    $.when(form_refresh(), result_refresh()).then($("#predicate").predautocomplete());
    // console.log(predicateIDlist);
  });
  // ******************************** query events **************************************//
  // send query parameters to the server
  $("#query").click(function () {
    console.log('sub: '+subjectID+'\nobj: '+objectID+'\npred: '+predicateID+'\noption: '+option);
    // console.log(subjectIDlist);
    // console.log(objectIDlist);
    // display warning message
    if (subjectID.length === 0 && objectID.length === 0 && predicateID.length === 0){
      $('#formalert').children().replaceWith("<div class='alert alert-danger alert-dismissible col-sm-8'> <strong>Warning!</strong> Empty fields are not allowed! <button type='button' class='close' aria-label='close'> <span aria-hidden='true'>&times;</span> </button></div>");
      $('#formalert').show();
    }
    else if (subjectID.length === 0 && objectID.length === 0){
      $('#formalert').children().replaceWith("<div class='alert alert-danger alert-dismissible col-sm-8'><strong>Warning!</strong> Subject and Object fields cannot both be empty! <button type='button' class='close' aria-label='close'> <span aria-hidden='true'>&times;</span> </button></div>");
      $('#formalert').show();
    }
    else if (predicateID.length === 0){
      $('#formalert').children().replaceWith("<div class='alert alert-danger alert-dismissible col-sm-8'><strong>Warning!</strong> Predicate field cannot be empty! <button type='button' class='close' aria-label='close'> <span aria-hidden='true'>&times;</span> </button></div>");
      $('#formalert').show();
    }
    else{  
      var msg = "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong>Hold on to your seats, we are fetching the results!</div>";
      displayinfo(msg); 
      result_refresh();
      $.ajax({
        type: 'GET',
        url: flaskurl,
        contentType: 'application/json',
        dataType: 'json',
        data: {
          'option': option,
          'subject': subjectID,
          'predicate': predicateID,
          'object': objectID 
        },
        success: function(result, status){
          // console.log(result);
          // console.log(status);
          var msg = "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong> Hope the results satisfy your curiosity!</div>";
          displayinfo(msg);
          displayresponse(result);
        },
        error: function(){
          console.log('error in flask get');
        }
      }); 
    }
  });
  // hide alert meassages
  $("[data-hide]").on("click", function(){
    $("#" + $(this).attr("data-hide")).hide();
    // -or-, see below
    // $(this).closest("." + $(this).attr("data-hide")).hide()
  });

  // ******************************** pre-defined queries ******************************//
  $('#example1').on('click', function () {
    var payload = {
      waitmsg: "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong>Hold on to your seats, we are fetching the results!</div>",
      subject: "Grey's Anatomy",
      subjectID: "Q438406",
      predicate: "P170: creator",
      object: "",
      kbname: 'wikidata',
      endmsg: "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong> Hope the results satisfy your curiosity!</div>"
    };
    samplequeries(payload);
  });

  $('#example2').on('click', function () {
    var payload = {
      waitmsg: "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong>Hold on to your seats, we are fetching the results!</div>",
      subject: "McGill University",
      subjectID: "https://en.wikipedia.org/wiki/McGill_University",
      predicate: "dbo: faculty size",
      object: "",
      kbname: "dbpedia",
      endmsg: "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong> Hope the results satisfy your curiosity!</div>"
    };
    samplequeries(payload);
  });

  $('#example3').on('click', function () {
    var payload = {
      waitmsg: "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong>Hold on to your seats, we are fetching the results!</div>",
      subject: "World War I",
      subjectID: "Q361",
      predicate: "P1120: number of deaths",
      object: "",
      kbname: "wikidata",
      endmsg: "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong> Hope the results satisfy your curiosity!</div>"
    };
    samplequeries(payload);
  });

  $('#example4').on('click', function () {
    var payload = {
      waitmsg: "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong>Hold on to your seats, we are fetching the results!</div>",
      subject: "Frankfurt Airport",
      subjectID: "http://wikipedia.org/wiki/Frankfurt_Airport",
      predicate: "dbo: hub airport",
      object: "",
      kbname: "dbpedia",
      endmsg: "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong> Hope the results satisfy your curiosity!</div>"
    };
    samplequeries(payload);
  });
  
  $('#example5').on('click', function () {
    var payload = {
      waitmsg: "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong>Hold on to your seats, we are fetching the results!</div>",
      subject: "Game of Thrones",
      subjectID: "Q23572",
      predicate: "P179: series",
      object: "",
      kbname: "wikidata",
      endmsg: "<div class='alert alert-info alert-dismissible' style='margin-bottom: 0px'><strong>!!</strong> Hope the results satisfy your curiosity!</div>"
    };
    samplequeries(payload);
  });
  // ******************************** result events ******************************//
  // $("#p1").on('click', function () {
  //   if ($("#s1").is(":hidden")) {
  //     $("#s1").show();
  //   }
  //   else {
  //     $("#s1").hide(); 
  //   }
  //   if ($("#o1").is(":hidden")) {    
  //     $("#o1").show();
  //   }
  //   else {
  //     $("#o1").hide();
  //   }
  // });
  // $(".p2").on('click', function () {
  //   alert('clicked');
  // });

});
