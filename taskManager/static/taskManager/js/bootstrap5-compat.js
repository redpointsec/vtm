/*
 * Local Bootstrap 5 compatibility behavior for the migration period.
 * It intentionally avoids jQuery and does not change route, form, or security
 * behavior in the vulnerable training app.
 */
(function () {
    "use strict";

    function closest(element, selector) {
        if (!element) {
            return null;
        }
        return element.closest(selector);
    }

    function getTarget(toggle) {
        var selector = toggle.getAttribute("data-bs-target") ||
            toggle.getAttribute("data-target") ||
            toggle.getAttribute("href");

        if (!selector || selector === "#") {
            return null;
        }

        if (selector.charAt(0) !== "#") {
            return null;
        }

        try {
            return document.querySelector(selector);
        } catch (error) {
            return null;
        }
    }

    function setExpanded(toggle, expanded) {
        toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
    }

    function closeDropdowns(except) {
        document.querySelectorAll(".dropdown-menu.show").forEach(function (menu) {
            var dropdown = closest(menu, ".dropdown");
            if (dropdown === except) {
                return;
            }
            menu.classList.remove("show");
            if (dropdown) {
                dropdown.classList.remove("open");
                var toggle = dropdown.querySelector("[data-bs-toggle='dropdown'], [data-toggle='dropdown']");
                if (toggle) {
                    setExpanded(toggle, false);
                }
            }
        });
    }

    function toggleDropdown(toggle) {
        var dropdown = closest(toggle, ".dropdown");
        var menu = dropdown ? dropdown.querySelector(".dropdown-menu") : null;

        if (!dropdown || !menu) {
            return;
        }

        var willOpen = !menu.classList.contains("show");
        closeDropdowns(dropdown);
        menu.classList.toggle("show", willOpen);
        dropdown.classList.toggle("open", willOpen);
        setExpanded(toggle, willOpen);
    }

    function toggleCollapse(toggle) {
        var target = getTarget(toggle);

        if (!target) {
            return;
        }

        var willOpen = !target.classList.contains("show");
        target.classList.toggle("show", willOpen);
        target.classList.toggle("in", willOpen);
        setExpanded(toggle, willOpen);
    }

    function toggleSidebar(toggle) {
        var willOpen = !document.body.classList.contains("sidebar-open");
        document.body.classList.toggle("sidebar-open", willOpen);
        document.body.classList.toggle("sidebar-close", !willOpen);
        var container = document.getElementById("container");
        if (container) {
            container.classList.toggle("sidebar-close", !willOpen);
        }
        setExpanded(toggle, willOpen);
    }

    function toggleSubMenu(link) {
        var item = closest(link, ".sub-menu");
        var submenu = item ? item.querySelector(".sub") : null;

        if (!item || !submenu) {
            return;
        }

        var willOpen = !submenu.classList.contains("show");
        submenu.classList.toggle("show", willOpen);
        item.classList.toggle("active", willOpen);
        setExpanded(link, willOpen);
    }

    function normalizeDateInput() {
        var input = document.getElementById("datetimepicker");

        if (!input || input.tagName !== "INPUT") {
            return;
        }

        if (!input.getAttribute("type") || input.getAttribute("type") === "text") {
            try {
                input.setAttribute("type", "date");
            } catch (error) {
                return;
            }
        }
    }

    function dismissElement(toggle) {
        var dismissType = toggle.getAttribute("data-bs-dismiss") || toggle.getAttribute("data-dismiss");
        var target = getTarget(toggle);

        if (!target && dismissType) {
            target = closest(toggle, "." + dismissType);
        }

        if (!target) {
            return;
        }

        target.classList.remove("show", "in");
        target.setAttribute("hidden", "hidden");
    }

    document.addEventListener("click", function (event) {
        var dropdownToggle = closest(event.target, "[data-bs-toggle='dropdown'], [data-toggle='dropdown']");
        var collapseToggle = closest(event.target, "[data-bs-toggle='collapse'], [data-toggle='collapse']");
        var dismissToggle = closest(event.target, "[data-bs-dismiss], [data-dismiss]");
        var sidebarToggle = closest(event.target, "[data-vtm-sidebar-toggle]");
        var subMenuLink = closest(event.target, "#sidebar .sub-menu > a");

        if (dropdownToggle) {
            event.preventDefault();
            toggleDropdown(dropdownToggle);
            return;
        }

        if (collapseToggle) {
            event.preventDefault();
            toggleCollapse(collapseToggle);
            return;
        }

        if (dismissToggle) {
            event.preventDefault();
            dismissElement(dismissToggle);
            return;
        }

        if (sidebarToggle) {
            event.preventDefault();
            toggleSidebar(sidebarToggle);
            return;
        }

        if (subMenuLink && subMenuLink.getAttribute("href") === "javascript:;") {
            event.preventDefault();
            toggleSubMenu(subMenuLink);
            return;
        }

        if (!closest(event.target, ".dropdown")) {
            closeDropdowns(null);
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeDropdowns(null);
        }
    });

    document.addEventListener("DOMContentLoaded", normalizeDateInput);
}());
