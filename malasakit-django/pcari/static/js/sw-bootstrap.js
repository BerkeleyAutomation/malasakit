/* Script here installs a ServiceWorker located in a separate script, sw.js.
   Not sure what else will happen here.
*/

function main() {
    if ("serviceWorker" in navigator) {
        // TODO: Address hardcoded urls
        navigator.serviceWorker.register('/pcari/sw.js')
            .then(function(registration) {
            // Registration successful
            console.log("Registration successful, SW scope: ",
                        registration.scope);
        }, function(err) {
            // Registration failed
            console.log("Registration failed: ", err);
        });
    }
}

window.onload = function () {
    main();
};
