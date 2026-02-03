// This ensures the code only runs after the "Hello" element exists
document.addEventListener("DOMContentLoaded", () => {
    // 1. Set the name from sessionStorage (Your previous task)
    const name = sessionStorage.getItem('name');
    document.getElementById("name").innerText = `Hello ${name}!!`;

    // 2. Fetch the complex stats from our new API route
    fetch('/api/user_stats')
        .then(response => response.json())
        .then(data => {
            // Update the UI cards dynamically
            document.getElementById("solved-count").innerText = data.total_solved;
            document.getElementById("streak-count").innerText = `${data.streak}`;
            console.log(data.total_solved)
        });
});
document.querySelectorAll('#data-concept-id').forEach(async ()=>{
    data = await fetch('',{

    })
})
function openRoadmap(){
    window.location.href="/roadmap"
}