terraform {
    required_providers {
        google = {
            source  = "hashicorp/google"
            version = "~> 3.84.0"
        }

        archive = {
            source  = "hashicorp/archive"
            version = "~> 2.2.0"
        }
    }
}

provider "google" {
    project = var.project
    region  = var.region
}

data "archive_file" "LaRE_GCP" {
    type = "zip"

    source_dir  = "${path.module}/src"
    output_path = "${path.module}/LaRE_GCP.zip"
}

resource "google_storage_bucket" "bucket" {
    name = "lare-bucket"
}

resource "google_storage_bucket_object" "LaRE_zip" {
    name    = "LaRE_GCP.zip"
    bucket  = google_storage_bucket.bucket.name
    source  = data.archive_file.LaRE_GCP.output_path
}

resource "google_project_service" "cb" {
    project = var.project
    service = "cloudbuild.googleapis.com"

    disable_dependent_services  = true
    disable_on_destroy          = false
}

resource "google_cloudfunctions_function" "LaRE" {
    name    = "LaRE"
    runtime = "python39"

    available_memory_mb     = 128
    source_archive_bucket   = google_storage_bucket.bucket.name
    source_archive_object   = google_storage_bucket_object.LaRE_zip.name
    trigger_http            = true
    entry_point             = "handler"
}

resource "google_cloudfunctions_function_iam_member" "invoker" {
    project         = google_cloudfunctions_function.LaRE.project
    region          = google_cloudfunctions_function.LaRE.region
    cloud_function  = google_cloudfunctions_function.LaRE.name

    role    = "roles/cloudfunctions.invoker"
    member  = "allUsers"  
}