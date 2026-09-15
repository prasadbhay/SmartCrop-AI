const cropImage = document.querySelector("#cropImage");
const preview = document.querySelector("#preview");
const analyzeButton = document.querySelector("#analyzeButton");
const result = document.querySelector("#result");


// Image preview
cropImage.addEventListener("change", function () {

    const file = cropImage.files[0];

    if (file) {
        preview.src = URL.createObjectURL(file);
        preview.style.display = "block";
    }

});


// Analyze button
analyzeButton.addEventListener("click", scanCrop);


async function scanCrop() {

    const image = cropImage.files[0];

    if (!image) {
        alert("⚠️ Please upload a crop image first.");
        return;
    }

    result.innerHTML = "<p>🤖 AI analyzing crop...</p>";


    // Temporary AI result
    // Real AI model will be connected later
    const isHealthy = Math.random() > 0.5;

    const plantId = "P-" + Math.floor(100 + Math.random() * 900);

    let detectionResult;
    let confidence;
    let sprayRequired;


    if (isHealthy) {

        detectionResult = "Healthy";
        confidence = 94;
        sprayRequired = "No";

        result.innerHTML = `
            <h2>🟢 Healthy</h2>
            <p><b>Plant ID:</b> ${plantId}</p>
            <p><b>AI Confidence:</b> ${confidence}%</p>
            <p>No visible crop defect detected.</p>
            <p><b>Spraying:</b> ❌ Not Required</p>
        `;

    } else {

        detectionResult = "Diseased / Defected";
        confidence = 91;
        sprayRequired = "Yes";

        result.innerHTML = `
            <h2>🔴 Diseased / Defected</h2>
            <p><b>Plant ID:</b> ${plantId}</p>
            <p><b>AI Confidence:</b> ${confidence}%</p>
            <p>Possible crop health problem detected.</p>
            <p><b>Spraying:</b> ✅ Required</p>
        `;
    }


    // Save result to backend
    try {

        const response = await fetch(
            "http://127.0.0.1:5000/api/detections",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    plant_id: plantId,
                    result: detectionResult,
                    confidence: confidence,
                    spray_required: sprayRequired
                })
            }
        );

        const data = await response.json();

        console.log("Backend response:", data);

    } catch (error) {

        console.error("Backend error:", error);

        result.innerHTML += `
            <p style="color:red;">
                ⚠️ Detection result shown, but database save failed.
            </p>
        `;
    }

}