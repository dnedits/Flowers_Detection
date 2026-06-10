package com.example.flowersdetection;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.net.Uri;
import android.os.Bundle;
import android.provider.MediaStore;
import android.util.Log;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import android.view.View;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.core.content.FileProvider;

import com.bumptech.glide.Glide;
import com.bumptech.glide.load.engine.DiskCacheStrategy;

import java.io.File;
import java.util.Locale;
import java.util.List;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "FlowersDetectionDebug";

    private Button btnTakePhoto, btnSelectImage, btnUpload, btnClear;
    private ImageButton btnWebSite, btnTelegram;
    private ImageView imageViewResult;
    private TextView tvResult, tvObjectCount;
    private ProgressBar progressBar;

    private Uri selectedImageUri = null;
    private Uri cameraImageUri = null;

    private static final int CAMERA_PERMISSION_CODE = 101;

    private final ActivityResultLauncher<Intent> imagePickerLauncher =
            registerForActivityResult(new ActivityResultContracts.StartActivityForResult(), result -> {
                if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                    selectedImageUri = result.getData().getData();
                    imageViewResult.setImageURI(selectedImageUri);
                    tvResult.setText("Изображение выбрано. Нажмите «Распознать».");
                }
            });

    private final ActivityResultLauncher<Intent> cameraLauncher =
            registerForActivityResult(new ActivityResultContracts.StartActivityForResult(), result -> {
                if (result.getResultCode() == RESULT_OK && cameraImageUri != null) {
                    selectedImageUri = cameraImageUri;
                    imageViewResult.setImageURI(selectedImageUri);
                    tvResult.setText("Фото сделано. Нажмите «Распознать».");
                }
            });

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        btnTakePhoto = findViewById(R.id.btnTakePhoto);
        btnSelectImage = findViewById(R.id.btnSelectImage);
        btnUpload = findViewById(R.id.btnUpload);
        btnClear = findViewById(R.id.btnClear);
        btnWebSite = findViewById(R.id.btnWebSite);
        btnTelegram = findViewById(R.id.btnTelegram);
        imageViewResult = findViewById(R.id.imageViewResult);
        tvResult = findViewById(R.id.tvResult);
        progressBar = findViewById(R.id.progressBar);
        tvObjectCount = findViewById(R.id.tvObjectCount);

        btnTakePhoto.setOnClickListener(v -> checkCameraPermissionAndOpen());
        btnSelectImage.setOnClickListener(v -> openGallery());

        btnUpload.setOnClickListener(v -> {
            if (selectedImageUri == null) {
                Toast.makeText(this, "Сначала выберите фото", Toast.LENGTH_SHORT).show();
                return;
            }
            uploadImage(selectedImageUri);
        });

        btnClear.setOnClickListener(v -> clearScreen());

        btnWebSite.setOnClickListener(v -> {
            String url = "https://192.168.3.29:8002";
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
        });

        btnTelegram.setOnClickListener(v -> openTelegram("flowers_diplom_bot"));
    }

    private void openTelegram(String username) {
        String uri = "tg://resolve?domain=" + username;

        Intent baseIntent = new Intent(Intent.ACTION_VIEW, Uri.parse(uri));
        PackageManager pm = getPackageManager();

        List<ResolveInfo> apps = pm.queryIntentActivities(baseIntent, 0);

        if (apps != null && !apps.isEmpty()) {

            // Фильтр только Telegram-клиентов
            boolean hasTelegram = false;
            for (ResolveInfo app : apps) {
                String pkg = app.activityInfo.packageName;
                if (pkg.contains("telegram")) {
                    hasTelegram = true;
                    break;
                }
            }

            if (hasTelegram) {
                if (apps.size() == 1) {
                    startActivity(baseIntent);
                } else {
                    startActivity(Intent.createChooser(baseIntent, "Открыть через"));
                }
            } else {
                openTelegramInBrowser(username);
            }

        } else {
            openTelegramInBrowser(username);
        }
    }

    private void openTelegramInBrowser(String username) {
        String url = "https://t.me/" + username;
        startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
    }

    private void uploadImage(Uri uri) {
        try {
            setLoading(true);
            File file = FileUtils.getFileFromUri(this, uri);

            RequestBody requestFile = RequestBody.create(file, MediaType.parse("image/*"));
            MultipartBody.Part body = MultipartBody.Part.createFormData("file", file.getName(), requestFile);

            ApiService apiService = RetrofitClient.getApiService();
            apiService.uploadImage(body).enqueue(new Callback<PredictionResponse>() {

                @Override
                public void onResponse(@NonNull Call<PredictionResponse> call, @NonNull Response<PredictionResponse> response) {
                    setLoading(false);

                    try {
                        if (response.isSuccessful() && response.body() != null) {
                            handleSuccessResponse(response.body());
                        } else {
                            String errorText = "Нет данных";
                            if (response.errorBody() != null) {
                                errorText = response.errorBody().string();
                            }
                            tvResult.setText("Код ошибки: " + response.code() + "\n" + errorText);
                        }
                    } catch (Exception e) {
                        tvResult.setText("Ошибка обработки: " + e.getMessage());
                    }
                }

                @Override
                public void onFailure(@NonNull Call<PredictionResponse> call, @NonNull Throwable t) {
                    setLoading(false);
                    tvResult.setText("Ошибка сети: " + t.getMessage());
                }
            });

        } catch (Exception e) {
            setLoading(false);
            tvResult.setText("Ошибка: " + e.getMessage());
        }
    }

    private void handleSuccessResponse(PredictionResponse result) {
        if (result.isSuccess()) {

            tvObjectCount.setText("Найдено: " + result.getCount());

            StringBuilder sb = new StringBuilder();
            if (result.getDetections() != null) {
                for (Detection d : result.getDetections()) {
                    sb.append("🔹 ")
                            .append(d.getClass_name())
                            .append(" (")
                            .append(String.format(Locale.US, "%.1f", d.getConfidence()))
                            .append("%)\n");
                }
            }

            tvResult.setText(sb.length() > 0 ? sb.toString() : "Объекты не найдены");

            if (result.getResult_image_url() != null) {
                String fullUrl = RetrofitClient.BASE_URL.replaceAll("/$", "") + result.getResult_image_url();

                Glide.with(this)
                        .load(fullUrl)
                        .override(1024, 1024)
                        .into(imageViewResult);
            }

            animateResultAppearance();

        } else {
            tvResult.setText("Ошибка сервера: " + result.getError());
        }
    }


    private void setLoading(boolean isLoading) {
        progressBar.setVisibility(isLoading ? View.VISIBLE : View.GONE);
        btnUpload.setEnabled(!isLoading);
    }

    private void animateResultAppearance() {
        imageViewResult.setAlpha(0f);
        imageViewResult.animate().alpha(1f).setDuration(500).start();
    }

    private void openGallery() {
        Intent intent = new Intent(Intent.ACTION_PICK, MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
        imagePickerLauncher.launch(intent);
    }

    private void checkCameraPermissionAndOpen() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            openCamera();
        } else {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION_CODE);
        }
    }

    private void openCamera() {
        try {
            File imageFile = File.createTempFile("camera_", ".jpg", getCacheDir());
            cameraImageUri = FileProvider.getUriForFile(this, getPackageName() + ".provider", imageFile);

            Intent intent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
            intent.putExtra(MediaStore.EXTRA_OUTPUT, cameraImageUri);
            intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION);

            cameraLauncher.launch(intent);

        } catch (Exception e) {
            Toast.makeText(this, "Ошибка камеры: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    private void clearScreen() {
        selectedImageUri = null;
        imageViewResult.setImageDrawable(null);
        tvObjectCount.setText("Найдено объектов: 0");
        tvResult.setText("Выберите изображение");
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);

        if (requestCode == CAMERA_PERMISSION_CODE
                && grantResults.length > 0
                && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            openCamera();
        }
    }
}