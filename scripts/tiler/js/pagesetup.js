/************************************************
 * Edmund's javascript loader
 *
 * This is a simplified version of Edmund's
 * javascript loader. 
 *
 * http://technology.edmunds.com/blog/javascript/
 *
 ***********************************************/

PAGESETUP = {timer: {start: (new Date()).getTime(), load_evt: -1}};

PAGESETUP.files = [];
PAGESETUP.combined_libs = {
};
PAGESETUP.breakdown_libs = [
];
PAGESETUP.modules = {};
PAGESETUP.queue = {high:[], normal:[], low:[]};
PAGESETUP.scope = {}; 
PAGESETUP.addModule = function(mod) {
    if (PAGESETUP.modules[mod]) {
        ++PAGESETUP.modules[mod];
    } else {
        PAGESETUP.modules[mod] = 1;
    }
};

PAGESETUP.execControls = function(start) {
    if (!PAGESETUP.timer.chunk_exec_start) {PAGESETUP.timer.chunk_exec_start = (new Date()).getTime() - PAGESETUP.timer.start;}
    var start = start || 0;
    if (!this.merged) {
        this.merged = PAGESETUP.queue.high;
        this.merged = this.merged.concat(PAGESETUP.queue.normal).concat(PAGESETUP.queue.low);
    } 
    var merged = this.merged;
    setTimeout(function() {
        var item = merged.shift();
        if (merged.length > 0) {
            setTimeout(arguments.callee, 25);
        } else {
            PAGESETUP.timer.chunk_exec_end = (new Date()).getTime() - PAGESETUP.timer.start;
        }
        item.call();
    }, 0);
};

PAGESETUP.addControl = function(fn, priority) {
     switch(priority) {
         case 'high':
            this.queue.high.push(fn);
         break;
         case 'low':
            this.queue.low.push(fn);
         break;
         case 'normal':
         default:
            this.queue.normal.push(fn);
         break;
     }
};

window.onload = function() {
	PAGESETUP.timer.load_evt = (new Date()).getTime() - PAGESETUP.timer.start;
};
