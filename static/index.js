const handleLogin = async() =>{
    const user_name = document.getElementById("user_name").value
    const user_pass = document.getElementById("user_pass").value
    console.log(user_name)
    console.log(user_pass)
    
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
    
    sessionStorage.setItem("name",data['name'])
    setTimeout(() => {
        window.location.href = "/dashboard"; 
    }, 3000);
} else {
    // document.getElementById("msg").innerText = data["message"];
    // document.getElementById("msg").style.color = "red";
}
}
const btn = document.getElementById('loginbtn');
console.log(btn)
// console.log(document.getElementById("username").value)
// 2. Add the "Ear" (Listener)
if (btn){
btn.addEventListener('click', handleLogin);}
// Registration
const handleRegistration = async() => {
    const user_name =document.getElementById("username").value
    const user_pass =document.getElementById("userpass").value
    const email  =document.getElementById("email").value

    console.log(user_name)
    console.log(user_pass)
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
        console.log("HIII")
    // loadOverlay()
        window.location.href = "/dashboard"; 
} else {
    // document.getElementById("msg").innerText = data["message"];
    // document.getElementById("msg").style.color = "red";
}
}
const regbtm = document.getElementById('regbtn');
// 2. Add the "Ear" (Listener)
if (regbtm){
    regbtm.addEventListener('click', handleRegistration);}
const loadOverlay = () => {
    document.getElementById("loading-overlay").style.display="flex"
}