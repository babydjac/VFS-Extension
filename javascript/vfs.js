document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll("button");
    buttons.forEach(button => {
        button.addEventListener("click", () => {
            button.classList.add("active");
            setTimeout(() => button.classList.remove("active"), 100);
        });
    });
});