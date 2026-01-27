const handleLogin = async() =>{
    const user_name = document.getElementById("user_name").value
    const user_pass = document.getElementById("user_pass").value
    const response = await fetch("/login",{
        method : "POST",
        headers : {"Content-Type":"application/JSON"},
        body : JSON.stringify({
            username : user_name,
            userpass : user_pass
        })
    })
    data = await response.json()
    console.log(data)
     if (response.ok) {
    loadOverlay()
    
    sessionStorage.setItem("name",data['name'])
    setTimeout(() => {
        window.location.href = "/dashboard"; 
    }, 3000);
} else {
    document.getElementById("msg").innerText = data["message"];
    document.getElementById("msg").style.color = "red";
}
}
const btn = document.getElementById('loginbtn');
// 2. Add the "Ear" (Listener)
if (btn){
btn.addEventListener('click', handleLogin);}
// Registration
const handleRegistration = async() => {
    const user_name =document.getElementById("user_name").value
    const user_pass =document.getElementById("user_pass").value
    const response = await fetch("/register",{
        method : "POST",
        headers : {
            "Content-Type":"application/JSON",
        },
        body : JSON.stringify({
            username : user_name,
            userpass : user_pass
        })
        }
    )
    data = await response.json() 
    console.log(data)
    if (response.ok) {
    loadOverlay()
    setTimeout(() => {
        window.location.href = "/dashboard"; 
    }, 3000);
} else {
    document.getElementById("msg").innerText = data["message"];
    document.getElementById("msg").style.color = "red";
}
}
const regbtm = document.getElementById('regbtn');
// 2. Add the "Ear" (Listener)
if (regbtm){
    regbtm.addEventListener('click', handleRegistration);}
const loadOverlay = () => {
    document.getElementById("loading-overlay").style.display="flex"
}