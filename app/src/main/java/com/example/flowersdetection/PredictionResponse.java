package com.example.flowersdetection;

import java.util.List;

public class PredictionResponse {
    private boolean success;
    private String filename;
    private int count;
    private List<Detection> detections;
    private String original_image_url;
    private String result_image_url;
    private String error;

    public boolean isSuccess() {
        return success;
    }

    public String getFilename() {
        return filename;
    }

    public int getCount() {
        return count;
    }

    public List<Detection> getDetections() {
        return detections;
    }

    public String getOriginal_image_url() {
        return original_image_url;
    }

    public String getResult_image_url() {
        return result_image_url;
    }

    public String getError() {
        return error;
    }
}
