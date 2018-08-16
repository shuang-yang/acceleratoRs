exports.ms_to_std_time = function (time_in_ms) {
	console.log('timeinms: ' + String(time_in_ms));
	var time_in_s = Math.floor(time_in_ms / 1000);
	console.log('timeinseconds: ' + String(time_in_s));
	// var ms_component = get_ms_component(time_in_ms);
	var ms_component = '';
	var std_time_in_s = time_in_s % 60;
	console.log('second: ' + String(std_time_in_s));
	var std_time_in_s_str = (std_time_in_s >= 10 ? String(std_time_in_s) : '0' + String(std_time_in_s));
	console.log('second string: ' + std_time_in_s_str);
    var std_time_in_min = Math.floor((time_in_s - std_time_in_s) % 3600 / 60);
	var std_time_in_min_str = (std_time_in_min >= 10 ? String(std_time_in_min) : '0' + String(std_time_in_min));
    var std_time_in_hr = Math.floor((time_in_s - std_time_in_min * 60 - std_time_in_s) / 3600);
    var std_time_in_hr_str = (std_time_in_hr >= 10 ? String(std_time_in_hr) : '0' + String(std_time_in_hr));
    var std_time = std_time_in_hr_str + ':' + std_time_in_min_str + ':' + std_time_in_s_str + '.' + ms_component;
    return std_time;
};

function get_ms_component(time_in_ms) {
	var time_in_ms_str = String(time_in_ms);
	var ms_component = time_in_ms >= 100 ? time_in_ms_str.slice(Math.max(time_in_ms_str.length - 5, 1)) : String(time_in_ms);
	while (ms_component.length < 3) {
		ms_component = '0' + ms_component;
	}
	return ms_component;
}