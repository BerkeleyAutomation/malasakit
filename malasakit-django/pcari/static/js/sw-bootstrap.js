/** sw-bootstrap.js -- Installs a service worker for caching pages for use offline
 */

const SERVICE_WORKER_SCRIPT_URL = '/sw.js';

window.onload = function() {
    if ('serviceWorker' in navigator) {
        // TODO: Address hardcoded urls
        navigator.serviceWorker.register(SERVICE_WORKER_SCRIPT_URL)
            .then(function(registration) {
                console.log('Registration successful, SW scope:',
                            registration.scope);
                registration.update();  // Try to update `sw.js`
        }, function(error) {
            console.log('Registration failed:', error);
        });
    }
}
