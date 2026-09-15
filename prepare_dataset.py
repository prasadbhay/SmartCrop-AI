import os
import random
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCE = os.path.join(
    os.path.expanduser("~"),
    "Downloads",
    "archive",
    "PlantVillage"
)

DATASET = os.path.join(BASE_DIR, "dataset")

# Clean old train/val images
for folder in [
    "dataset/train/Healthy",
    "dataset/train/Diseased",
    "dataset/val/Healthy",
    "dataset/val/Diseased"
]:
    path = os.path.join(BASE_DIR, folder)

    if os.path.exists(path):
        for file in os.listdir(path):
            file_path = os.path.join(path, file)

            if os.path.isfile(file_path):
                os.remove(file_path)


healthy_source = os.path.join(SOURCE, "Potato___healthy")
early_source = os.path.join(SOURCE, "Potato___Early_blight")
late_source = os.path.join(SOURCE, "Potato___Late_blight")


train_healthy = os.path.join(DATASET, "train", "Healthy")
train_diseased = os.path.join(DATASET, "train", "Diseased")

val_healthy = os.path.join(DATASET, "val", "Healthy")
val_diseased = os.path.join(DATASET, "val", "Diseased")


os.makedirs(train_healthy, exist_ok=True)
os.makedirs(train_diseased, exist_ok=True)
os.makedirs(val_healthy, exist_ok=True)
os.makedirs(val_diseased, exist_ok=True)


def get_images(folder):

    return [
        os.path.join(folder, file)
        for file in os.listdir(folder)
        if file.lower().endswith((".jpg", ".jpeg", ".png"))
    ]


healthy = get_images(healthy_source)
early = get_images(early_source)
late = get_images(late_source)


random.seed(42)

random.shuffle(healthy)
random.shuffle(early)
random.shuffle(late)


# Use 152 images from each class
healthy = healthy[:152]
early = early[:152]
late = late[:152]


# 80% training / 20% validation
healthy_train = healthy[:121]
healthy_val = healthy[121:]

early_train = early[:121]
early_val = early[121:]

late_train = late[:121]
late_val = late[121:]


def copy_files(files, destination):

    for index, file in enumerate(files):

        extension = os.path.splitext(file)[1]

        new_name = f"potato_{index:04d}{extension}"

        shutil.copy2(
            file,
            os.path.join(destination, new_name)
        )


copy_files(healthy_train, train_healthy)
copy_files(healthy_val, val_healthy)

copy_files(early_train, train_diseased)
copy_files(late_train, train_diseased)

copy_files(early_val, val_diseased)
copy_files(late_val, val_diseased)


print("===================================")
print("Potato dataset prepared successfully!")
print("===================================")

print("Train Healthy:", len(healthy_train))
print("Train Diseased:", len(early_train) + len(late_train))

print("Validation Healthy:", len(healthy_val))
print("Validation Diseased:", len(early_val) + len(late_val))

print("===================================")