// color variables:
//	var ms_blue='#152F81';
//	var ms_lightgray='#BECDD7';
//	var ms_darkgray='#404A57';
//	var ms_red='#C00000';
//	var ms_orange='#EB780A';
//	var ms_green='#647D2D';


function update_dashboard(name_symbol) {
    // alert('Now changing to: ' + sym);
    document.getElementById('q').value = name_symbol;
    // alert('Form filled with dymbol');
    document.change_stock.submit();
    return 0;
};

// Execute when the DOM is fully loaded
$(document).ready(function() {

    configure();
});


// Configure application
function configure() {

    // Configure typeahead
    $("#q").typeahead({
        highlight: false,
        name: 'q',
        minLength: 1,
        hint: true
    }, {
        display: function(suggestion) { return null; },
        limit: 10,

        valueKey: "symbol",
        source: search,
        templates: {
            suggestion: Handlebars.compile("<div style=\"text-align:left;\">{{stock_name}} ({{symbol}})</div>")
        }
    });

    // Re-center map after place is selected from drop-down
    $("#q").on("typeahead:selected", function(eventObject, suggestion, name) {
        //var sel=document.getElementById("q").value;
        //document.getElementById('q').value=suggestion;
        // alert('Chosen element: ' + document.getElementById('q').value);
        // alert('You selected something: ' + suggestion.symbol);
        update_dashboard(suggestion.symbol);
        // alert('I called update dashboard');
    });

    // Give focus to text box
    $("#q").focus();
}

// Search database for typeahead's suggestions
function search(query, syncResults, asyncResults) {
    // Get places matching query (asynchronously)
    let parameters = {
        q: query
    };
    $.getJSON("/search", parameters, function(data, textStatus, jqXHR) {

        // Call typeahead's callback with search results (i.e. stocks)
        asyncResults(data);
    });
}
