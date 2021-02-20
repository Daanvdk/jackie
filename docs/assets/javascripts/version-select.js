function checkExists(link, href) {
    var xhr = new XMLHttpRequest();
    xhr.open("HEAD", href);
    xhr.onload = function() {
        if (this.status === 200) {
            link.href = href;
        }
    }
    xhr.send();
}

window.addEventListener("DOMContentLoaded", function() {
    // This is a bit hacky. Figure out the base URL from a known CSS file the
    // template refers to...
    var ex = new RegExp("/?assets/stylesheets/base.css$");
    var sheet = document.querySelector('link[href$="base.css"]');

    var HOST = window.location.protocol + '//' + window.location.host;
    var BASE_URL = sheet.href.replace(ex, "");
    if (BASE_URL.startsWith(HOST)) {
        BASE_URL = BASE_URL.slice(HOST.length);
    }

    var parts = BASE_URL.split('/');
    var CURRENT_VERSION = parts.pop();
    BASE_URL = parts.join("/");

    var xhr = new XMLHttpRequest();
    xhr.open("GET", BASE_URL + "/versions.json");
    xhr.onload = function() {
        var versions = JSON.parse(this.responseText);

        var currentVersion = versions.find(function(i) {
            return (
                i.version === CURRENT_VERSION ||
                i.aliases.includes(CURRENT_VERSION)
            );
        });

        var sidebar = document.querySelector(".md-nav--primary > .md-nav__list");
        { // Container
            var container = document.createElement("li");
            container.className = "md-nav__item md-nav__item--nested";
            { // Checkbox
                var checkbox = document.createElement("input");
                checkbox.id = "version-select";
                checkbox.className = "md-nav__toggle md-toggle";
                checkbox.type = "checkbox";
                checkbox.setAttribute("data-md-toggle", "version-select");

                container.appendChild(checkbox);
            }
            { // Label
                var label = document.createElement("label");
                label.className = "md-nav__link";
                label.setAttribute('for', 'version-select');

                var text = document.createTextNode("Version: " + currentVersion.title);
                label.appendChild(text);

                var icon = document.createElement("span");
                icon.className = "md-nav__icon md-icon";
                label.appendChild(icon);

                container.appendChild(label);
            }
            { // Nav
                var nav = document.createElement("nav");
                nav.className = "md-nav";
                nav.setAttribute("aria-label", "Version: " + currentVersion.title);
                nav.setAttribute("data-md-level", "1");
                { // Label
                    var label = document.createElement("label");
                    label.className = "md-nav__title";
                    label.setAttribute("for", "version-select");

                    var icon = document.createElement("span");
                    icon.className = "md-nav__icon md-icon";
                    label.appendChild(icon);

                    var text = document.createTextNode("Version: " + currentVersion.title);
                    label.appendChild(text);

                    nav.appendChild(label);
                }
                var VERSION_URL = BASE_URL + "/" + currentVersion.version;
                { // List
                    var list = document.createElement("ul");
                    list.className = "md-nav__list";
                    for (let i = 0; i < versions.length; i++) {
                        var active = versions[i].version === currentVersion.version;

                        var title = versions[i].title;
                        if (versions[i].aliases.length > 0) {
                            title += " (";
                            for (let j = 0; j < versions[i].aliases.length; j++) {
                                if (j !== 0) {
                                    title += ", ";
                                }
                                title += versions[i].aliases[j];
                            }
                            title += ")";
                        }

                        var text = document.createTextNode(title);

                        var link = document.createElement("a");
                        link.className = "md-nav__link" + (active ? " md-nav__link--active" : "");
                        link.href = BASE_URL + "/" + versions[i].version;
                        link.appendChild(text);

                        var item = document.createElement("li");
                        item.className = "md-nav__item" + (active ? " md-nav__item--active" : "");
                        item.appendChild(link);

                        list.appendChild(item);

                        if (window.location.pathname.startsWith(VERSION_URL)) {
                            checkExists(link, (
                                BASE_URL + "/" + versions[i].version +
                                window.location.pathname.slice(VERSION_URL.length)
                            ));
                        }
                    }
                    nav.appendChild(list);
                }
                container.appendChild(nav);
            }
            sidebar.appendChild(container);
        }
    };
    xhr.send();
});
