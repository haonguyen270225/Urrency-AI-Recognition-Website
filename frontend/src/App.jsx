
import { useRef, useState } from "react";
import "./App.css";
import { predictBatch } from "./services/predictionService";

const AI_MODELS = [
  { id: "custom_cnn", name: "Custom CNN" },
  { id: "mobilenetv2", name: "MobileNetV2" },
  { id: "resnet", name: "ResNet18" },
  { id: "random_forest", name: "Random Forest" },
  { id: "yolo", name: "YOLO11" },
];

const MAX_IMAGES = 20;
const MAX_FILE_SIZE = 10 * 1024 * 1024;

const createId = () =>
  `${Date.now()}-${Math.random().toString(36).slice(2)}`;

const formatConfidence = (value) => {
  const number = Number(value);

  if (!Number.isFinite(number)) return "0.00";

  return number.toFixed(2);
};

const formatDenomination = (value) => {
  if (value === null || value === undefined || value === "") {
    return "Không xác định";
  }

  const number = Number(value);

  if (Number.isFinite(number) && typeof value !== "boolean") {
    return number.toLocaleString("en-US");
  }

  return String(value);
};

const getTopPredictionConfidence = (item) => {
  const value = item.confidence ?? item.probability ?? item.score;

  if (value === null || value === undefined) return null;

  let number = Number(value);

  if (!Number.isFinite(number)) return null;

  // Một số service trả xác suất trong khoảng 0 đến 1.
  if (number >= 0 && number <= 1) {
    number *= 100;
  }

  return number;
};

function App() {
  const fileInputRef = useRef(null);

  const [selectedFiles, setSelectedFiles] = useState([]);
  const [selectedModel, setSelectedModel] = useState("custom_cnn");
  const [results, setResults] = useState([]);
  const [history, setHistory] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState("home");
  const [dragging, setDragging] = useState(false);

  // Tải lên một hoặc nhiều ảnh.
  const handleFiles = (fileList) => {
    const files = Array.from(fileList || []);

    if (files.length === 0) return;

    const remainingSlots = MAX_IMAGES - selectedFiles.length;

    if (remainingSlots <= 0) {
      alert(`Mỗi lần chỉ được chọn tối đa ${MAX_IMAGES} ảnh.`);
      return;
    }

    const validFiles = [];
    let invalidCount = 0;

    files.forEach((file) => {
      const allowedTypes = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/bmp",
      ];

      if (
        !allowedTypes.includes(file.type) ||
        file.size > MAX_FILE_SIZE
      ) {
        invalidCount++;
        return;
      }

      validFiles.push(file);
    });

    if (invalidCount > 0) {
      alert(
        `${invalidCount} ảnh không hợp lệ. Chỉ hỗ trợ JPG, JPEG, PNG, WEBP, BMP và dung lượng tối đa 10MB.`
      );
    }

    const acceptedFiles = validFiles.slice(0, remainingSlots);

    if (validFiles.length > remainingSlots) {
      alert(
        `Bạn chỉ có thể thêm ${remainingSlots} ảnh nữa. Giới hạn là ${MAX_IMAGES} ảnh.`
      );
    }

    const newFiles = acceptedFiles.map((file) => ({
      id: createId(),
      file,
      preview: URL.createObjectURL(file),
    }));

    setSelectedFiles((previous) => [...previous, ...newFiles]);
  };

  // Xóa một ảnh.
  const removeFile = (id) => {
    setSelectedFiles((previous) => {
      const target = previous.find((item) => item.id === id);

      if (target) {
        URL.revokeObjectURL(target.preview);
      }

      return previous.filter((item) => item.id !== id);
    });
  };

  // Xóa tất cả ảnh.
  const clearFiles = () => {
    selectedFiles.forEach((item) => {
      URL.revokeObjectURL(item.preview);
    });

    setSelectedFiles([]);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Nhận diện ảnh bằng Backend FastAPI.
  const handleAnalyze = async () => {
    if (selectedFiles.length === 0) {
      alert("Vui lòng chọn ít nhất một ảnh!");
      return;
    }

    if (selectedFiles.length > MAX_IMAGES) {
      alert(`Mỗi lần chỉ được nhận diện tối đa ${MAX_IMAGES} ảnh.`);
      return;
    }

    setIsAnalyzing(true);

    const startTime = performance.now();

    try {
      const files = selectedFiles.map((item) => item.file);

      const response = await predictBatch(files, selectedModel);

      const endTime = performance.now();

      const processingTime = (
        (endTime - startTime) /
        1000
      ).toFixed(2);

      if (!response.success || !Array.isArray(response.results)) {
        throw new Error(
          response.message || "Không nhận được kết quả nhận diện."
        );
      }

      const modelName =
        AI_MODELS.find((item) => item.id === selectedModel)?.name ||
        selectedModel;

      const mappedResults = response.results.map((item, index) => {
        const originalFile = files[index];

        const imageBase64 = item.image_base64
          ? `data:${originalFile?.type || "image/jpeg"};base64,${item.image_base64}`
          : selectedFiles[index]?.preview || "";

        return {
          id: createId(),

          fileName: item.filename || originalFile?.name || "Unknown",

          image: imageBase64,

          currency: item.currency || "Unknown",

          denomination:
            item.denomination_display ??
            item.denomination_label ??
            item.denomination ??
            "Không xác định",

          confidence: Number(item.confidence ?? 0),

          currencyConfidence:
            item.currency_confidence ?? null,

          denominationConfidence:
            item.denomination_confidence ?? null,

          denominationLabel: item.denomination_label ?? null,

          topPredictions: Array.isArray(item.top_predictions)
            ? item.top_predictions
            : [],

          model: modelName,

          processingTime,

          createdAt: new Date().toISOString(),
        };
      });

      setResults(mappedResults);

      setHistory((previousHistory) =>
        [...mappedResults, ...previousHistory].slice(0, 20)
      );

      setTimeout(() => {
        document
          .getElementById("results")
          ?.scrollIntoView({ behavior: "smooth" });
      }, 100);

    } catch (error) {
      console.error("Prediction error:", error);

      const message =
        error.response?.data?.detail ||
        error.message ||
        "Không thể kết nối với Backend.";

      alert(`Nhận diện thất bại: ${message}`);

    } finally {
      setIsAnalyzing(false);
    }
  };

  // Xuất lịch sử ra CSV.
  const exportCSV = () => {
    if (history.length === 0) {
      alert("Chưa có dữ liệu lịch sử để xuất.");
      return;
    }

    const headers = [
      "Ten anh",
      "Loai tien",
      "Menh gia",
      "Do tin cay",
      "Do tin cay loai tien",
      "Do tin cay menh gia",
      "Mo hinh",
      "Thoi gian",
    ];

    const rows = history.map((item) => [
      item.fileName,
      item.currency,
      item.denomination,
      `${formatConfidence(item.confidence)}%`,
      item.currencyConfidence == null
        ? "N/A"
        : `${formatConfidence(item.currencyConfidence)}%`,
      item.denominationConfidence == null
        ? "N/A"
        : `${formatConfidence(item.denominationConfidence)}%`,
      item.model,
      item.createdAt,
    ]);

    const csvContent = [headers, ...rows]
      .map((row) =>
        row
          .map((value) =>
            `"${String(value ?? "").replaceAll('"', '""')}"`
          )
          .join(",")
      )
      .join("\n");

    const blob = new Blob(["\uFEFF" + csvContent], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "currency-recognition-history.csv";
    link.click();

    URL.revokeObjectURL(url);
  };

  const scrollTo = (id, tab) => {
    setActiveTab(tab);

    document.getElementById(id)?.scrollIntoView({
      behavior: "smooth",
    });
  };

  return (
    <div className="app-container">
      {/* HEADER */}
      <header className="main-header">
        <div className="header-inner">
          <a href="#home" className="brand">
            <div className="brand-icon">✿</div>

            <div className="brand-name">
              <strong>Currency AI</strong>
              <span>RECOGNITION</span>
            </div>
          </a>

          <nav className="header-nav">
            <button
              className={activeTab === "home" ? "nav-link active" : "nav-link"}
              onClick={() => scrollTo("home", "home")}
            >
              Trang chủ
            </button>

            <button
              className={
                activeTab === "scanner" ? "nav-link active" : "nav-link"
              }
              onClick={() => scrollTo("scanner", "scanner")}
            >
              Nhận diện tiền
            </button>

            <button
              className={
                activeTab === "history" ? "nav-link active" : "nav-link"
              }
              onClick={() => scrollTo("history", "history")}
            >
              Lịch sử
            </button>

            <button
              className={activeTab === "about" ? "nav-link active" : "nav-link"}
              onClick={() => scrollTo("about", "about")}
            >
              Giới thiệu
            </button>
          </nav>

          <button
            className="header-action"
            onClick={() => scrollTo("scanner", "scanner")}
          >
            <span>✧</span> Bắt đầu nhận diện
          </button>
        </div>
      </header>

      <main>
        {/* HERO */}
        <section className="hero-section" id="home">
          <div className="hero-content">
            <div className="hero-badge">
              <span className="online-dot"></span>
              Mô hình thị giác AI · 3 loại tiền tệ
            </div>

            <h1>
              Nhận diện tiền giấy
              <br />
              <span>chỉ bằng một bức ảnh</span>
            </h1>

            <p className="hero-description">
              Tải lên một hoặc nhiều ảnh tiền, hệ thống sẽ xác định loại tiền tệ
              và mệnh giá tương ứng kèm độ tin cậy của mô hình.
            </p>

            <div className="hero-bottom">
              <button
                className="hero-button"
                onClick={() => scrollTo("scanner", "scanner")}
              >
                Tải ảnh lên ngay <span>↓</span>
              </button>

              <div className="hero-features">
                <span>◉ VND · USD · CNY</span>
                <span>ϟ Kết quả trong vài giây</span>
                <span>✧ Độ tin cậy theo từng ảnh</span>
              </div>
            </div>
          </div>
        </section>

        {/* UPLOAD */}
        <section className="scanner-section" id="scanner">
          <div className="upload-card">
            <div className="upload-card-header">
              <div>
                <h2>Tải ảnh tiền giấy</h2>
                <p>Hỗ trợ JPG, JPEG, PNG, WEBP và BMP · Tối đa 20 ảnh/lần</p>
              </div>

              <span className="image-count">
                ▧ &nbsp;{selectedFiles.length}/{MAX_IMAGES} ảnh đã chọn
              </span>
            </div>

            <div className="upload-card-body">
              {/* MODEL SELECT */}
              <div className="model-select-row">
                <div className="model-label">
                  <div className="model-icon">⚙</div>
                  <div>
                    <strong>Mô hình phân loại</strong>
                    <span>Chọn 1 trong 5 mô hình cho lượt nhận diện</span>
                  </div>
                </div>

                <select
                  value={selectedModel}
                  onChange={(event) => setSelectedModel(event.target.value)}
                  disabled={isAnalyzing}
                >
                  {AI_MODELS.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* UPLOAD ZONE */}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp,image/bmp"
                multiple
                hidden
                onChange={(event) => {
                  handleFiles(event.target.files);
                  event.target.value = "";
                }}
              />

              <div
                className={`upload-zone ${dragging ? "dragging" : ""}`}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(event) => {
                  event.preventDefault();
                  setDragging(false);
                  handleFiles(event.dataTransfer.files);
                }}
                onClick={() => {
                  if (!isAnalyzing) {
                    fileInputRef.current?.click();
                  }
                }}
              >
                <div className="upload-illustration">
                  <span className="money-symbol symbol-one">$</span>
                  <span className="money-symbol symbol-two">₫</span>
                  <div className="upload-image-icon">▣</div>
                </div>

                <h3>Kéo & thả ảnh tiền giấy vào đây</h3>
                <p>hoặc chọn ảnh trực tiếp từ máy tính của bạn</p>

                <button
                  type="button"
                  className="upload-button"
                  disabled={isAnalyzing}
                  onClick={(event) => {
                    event.stopPropagation();
                    fileInputRef.current?.click();
                  }}
                >
                  <span>♧</span> Upload Images
                </button>

                <span className="upload-limit">
                  Có thể chọn nhiều ảnh cùng lúc · Tối đa 20 ảnh
                </span>
              </div>

              {/* SELECTED IMAGES */}
              {selectedFiles.length > 0 && (
                <div className="selected-images">
                  <div className="selected-images-heading">
                    <strong>Ảnh đã tải lên ({selectedFiles.length})</strong>

                    <button
                      type="button"
                      onClick={clearFiles}
                      disabled={isAnalyzing}
                    >
                      Xóa tất cả
                    </button>
                  </div>

                  <div className="image-grid">
                    {selectedFiles.map((item) => (
                      <div className="selected-image" key={item.id}>
                        <img src={item.preview} alt={item.file.name} />

                        <button
                          type="button"
                          className="remove-image"
                          onClick={() => removeFile(item.id)}
                          disabled={isAnalyzing}
                          aria-label="Xóa ảnh"
                        >
                          ×
                        </button>

                        <span title={item.file.name}>{item.file.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ACTION */}
              <div className="upload-actions">
                <span>
                  {selectedFiles.length > 0
                    ? `Đã sẵn sàng nhận diện ${selectedFiles.length} ảnh`
                    : "Chưa có hình ảnh nào được chọn"}
                </span>

                <button
                  className="recognize-button"
                  onClick={handleAnalyze}
                  disabled={selectedFiles.length === 0 || isAnalyzing}
                >
                  {isAnalyzing ? (
                    <>
                      <span className="spinner"></span>
                      Đang phân tích...
                    </>
                  ) : (
                    <>
                      ✧ &nbsp; Start Recognition <span>→</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* RESULTS */}
        <section className="results-section" id="results">
          <div className="section-title-row">
            <div>
              <h2>Kết quả nhận diện</h2>
              <p>
                Loại tiền tệ, mệnh giá và độ tin cậy · Mô hình{" "}
                <strong>
                  {AI_MODELS.find((item) => item.id === selectedModel)?.name}
                </strong>
              </p>
            </div>

            <button
              className="export-button"
              onClick={exportCSV}
              disabled={history.length === 0}
            >
              ↓ &nbsp; Xuất CSV
            </button>
          </div>

          {results.length === 0 ? (
            <div className="empty-results">
              <div className="empty-icon">✧</div>
              <h3>Chưa có kết quả nào</h3>
              <p>
                Tải ảnh tiền giấy lên và bấm "Start Recognition" để xem
                <br className="desktop-break" />
                kết quả tại đây.
              </p>
            </div>
          ) : (
            <div className="results-grid">
              {results.map((item, index) => (
                <article
                  className="result-card"
                  key={item.id}
                  style={{
                    animationDelay: `${Math.min(index * 120, 600)}ms`,
                  }}
                >
                  <div className="result-image">
                    <img src={item.image} alt={item.fileName} />
                    <span className="result-image-label">ẢNH DỰ ĐOÁN</span>
                  </div>

                  <div className="result-content">
                    <div className="result-topline">
                      <span className="result-success">
                        ✓ Nhận diện hoàn tất
                      </span>
                      <span className="result-currency">{item.currency}</span>
                    </div>

                    <div className="result-denomination">
                      {formatDenomination(item.denomination)}
                      {!String(item.denomination)
                        .toUpperCase()
                        .includes(String(item.currency).toUpperCase()) && (
                        <span> {item.currency}</span>
                      )}
                    </div>

                    <div className="confidence-row">
                      <span>Độ tin cậy tổng thể</span>
                      <strong>{formatConfidence(item.confidence)}%</strong>
                    </div>

                    <div className="confidence-track">
                      <div
                        className="confidence-value"
                        style={{
                          width: `${Math.min(
                            Math.max(Number(item.confidence) || 0, 0),
                            100,
                          )}%`,
                        }}
                      ></div>
                    </div>

                    {item.currencyConfidence != null && (
                      <div className="confidence-row">
                        <span>Độ tin cậy loại tiền</span>
                        <strong>
                          {formatConfidence(item.currencyConfidence)}%
                        </strong>
                      </div>
                    )}

                    {item.denominationConfidence != null && (
                      <div className="confidence-row">
                        <span>Độ tin cậy mệnh giá</span>
                        <strong>
                          {formatConfidence(item.denominationConfidence)}%
                        </strong>
                      </div>
                    )}

                    {/* TOP PREDICTIONS */}
                    {item.topPredictions.length > 0 && (
                      <div className="top-predictions">
                        <strong>Top dự đoán</strong>

                        <div className="prediction-list">
                          {item.topPredictions
                            .slice(0, 5)
                            .map((prediction, predictionIndex) => {
                              const label =
                                prediction.display ||
                                prediction.label ||
                                prediction.denomination ||
                                "Không xác định";

                              const predictionConfidence =
                                getTopPredictionConfidence(prediction);

                              return (
                                <div
                                  className="prediction-item"
                                  key={`${item.id}-${predictionIndex}`}
                                >
                                  <span className="prediction-rank">
                                    {predictionIndex + 1}
                                  </span>

                                  <span className="prediction-label">
                                    {label}
                                  </span>

                                  {predictionConfidence != null && (
                                    <strong>
                                      {formatConfidence(predictionConfidence)}%
                                    </strong>
                                  )}
                                </div>
                              );
                            })}
                        </div>
                      </div>
                    )}

                    <div className="result-meta">
                      <span>
                        Mô hình: <strong>{item.model}</strong>
                      </span>
                      <span>{item.processingTime}s</span>
                    </div>

                    <p className="result-filename" title={item.fileName}>
                      {item.fileName}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        {/* HISTORY */}
        <section className="history-section" id="history">
          <div className="section-title-row">
            <div>
              <span className="section-eyebrow">RECOGNITION HISTORY</span>
              <h2>Lịch sử nhận diện</h2>
              <p>
                Lưu lại những kết quả đã thực hiện trong phiên làm việc này.
              </p>
            </div>

            <button
              className="export-button"
              onClick={exportCSV}
              disabled={history.length === 0}
            >
              ↓ &nbsp; Xuất CSV
            </button>
          </div>

          {history.length === 0 ? (
            <div className="history-empty">
              <div className="empty-icon">◷</div>
              <h3>Lịch sử đang trống</h3>
              <p>Các kết quả nhận diện sẽ được hiển thị tại đây.</p>
            </div>
          ) : (
            <div className="history-list">
              {history.map((item) => (
                <div className="history-item" key={item.id}>
                  <img src={item.image} alt={item.fileName} />

                  <div className="history-info">
                    <strong>{item.fileName}</strong>
                    <span>
                      {new Date(item.createdAt).toLocaleString("vi-VN")}
                    </span>
                  </div>

                  <div className="history-prediction">
                    <strong>
                      {formatDenomination(item.denomination)}
                      {!String(item.denomination)
                        .toUpperCase()
                        .includes(String(item.currency).toUpperCase()) && (
                        <> {item.currency}</>
                      )}
                    </strong>
                    <span>{item.model}</span>
                  </div>

                  <div className="history-confidence">
                    {formatConfidence(item.confidence)}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* ABOUT */}
        <section className="about-section" id="about">
          <div>
            <span className="section-eyebrow">ABOUT OUR PROJECT</span>
            <h2>Currency AI Recognition</h2>
            <p>
              Ứng dụng trí tuệ nhân tạo và thị giác máy tính để nhận diện tiền
              giấy, xác định loại tiền tệ và mệnh giá từ hình ảnh.
            </p>
          </div>

          <div className="about-models">
            <strong>05</strong>
            <span>AI MODELS</span>
            <p>Machine Learning & Deep Learning</p>
          </div>
        </section>
      </main>

      {/* FOOTER */}
      <footer className="main-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <div className="brand-icon">✿</div>
            <strong>Currency AI Recognition</strong>
          </div>

          <p>© 2026 Currency AI Recognition. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
