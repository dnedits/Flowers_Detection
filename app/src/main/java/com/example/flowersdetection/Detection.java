package com.example.flowersdetection;

import java.util.List;

public class Detection {
    private int class_id;
    private String class_name;
    private double confidence;

    private List<Double> bbox;

    public int getClass_id() {
        return class_id;
    }

    public String getClass_name() {
        return class_name;
    }

    public double getConfidence() {
        return confidence;
    }

    public List<Double> getBbox() {
        return bbox;
    }
}