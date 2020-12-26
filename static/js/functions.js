$(document).ready(function(){
	var count = 1;
	var id_column = 'input';
	var max_length = document.getElementById("ol_field").getElementsByTagName("ol").length;
  $("#add_field").click(function(){
  alert(max_length);
  	var result = id_column+count.toString();
  	var result_dt = "input_dt"+count.toString();
  	var result_len = "input_len"+count.toString();
  	var i;
  	var max_num_column = 13 - max_length;
	if(count < max_num_column){
    $("#ol_field").append('<ol><input type="checkbox" id="checkbox" name="check" value="{{ item }}" style="margin-right:5px;"><input type="text" id="input" name="input"><select id="input_dt" name="input_dt" style="margin-left:4px;"><option type="text" value=""></option><option type="text" value="character" style="margin-left:5px;">character</option><option type="text" value="integer">integer</option></select><input type="text" id="input_len" name="input_len" value="" style="margin-left:4px;"></ol>');
	count++;
	var e = document.getElementById("input");
	var e_dt = document.getElementById("input_dt");
	var e_len = document.getElementById("input_len");
  	e.id = result;
  	e_dt.id = result_dt;
  	e_len.id = result_len;
  	e.name = result;
  	e_dt.name = result_dt;
  	e_len.name = result_len;

	div1 = document.getElementById("#ol_field");
	div1.style.height = div1.offsetHeight+"px";
	 var element = document.getElementById("row");
     element.scrollTop = element.scrollHeight;
     }
     else{
     	alert("Your reached the max number of columns.");
     }
    });
    });

function myFunction() {
  var elmnt = document.getElementById("bottom_btn");
  elmnt.scrollIntoView();
}

