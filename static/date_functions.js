var dates = document.getElementById("custom_dates");
var time_period = document.getElementById("time_period");
console.log(time_period.value)

var start_date = document.getElementById("start_date");
var end_date = document.getElementById("end_date");

time_period.addEventListener("change", function()
{
    console.log(time_period.value);
    if(time_period.value == "custom")
    {
        dates.style.display = "block";
    }
    else
    {
        dates.style.display = "none";
    }
});

// TODO: fix validation when writing down the date manually
end_date.addEventListener("input", function()
{
    if(time_period.value == "custom")
    {
        const start_value = new Date(start_date.value);
        const end_value = new Date(end_date.value);

        if(start_date.value && end_value < start_value)
        {
            alert("End date should be after the start date.");
            end_date.value = start_date.value;
        }

        const now = new Date();

        if(end_value > now)
        {
            alert("End date cannot be in the future.");
            end_date.value = now.toISOString().split('T')[0];
        }
    }
});
