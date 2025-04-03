from keras.models import Sequential
from keras.layers import Conv1D, MaxPooling1D, LSTM, Dense, Reshape
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
import matplotlib.pyplot as plt
# 读取数据
df = pd.read_csv("./data_set/all_typhoon_data.csv")

grouped = df.groupby("国际编号")
# 构建时间序列
def build_sequences(data, n_timesteps, n_future):
    X, y = [], []
    for _, group in grouped:
        group = group.sort_values("时间")  # 按时间排序
        features = group[["时间", "纬度", "经度", "等级", "中心最低气压", "2分钟平均风速"]].values
        targets = group[["时间", "纬度", "经度", "等级", "中心最低气压", "2分钟平均风速"]].values
        if len(features) < n_timesteps + n_future:
            continue  # 跳过数据不足的台风
        for i in range(len(features) - n_timesteps - n_future + 1):
            X.append(features[i:i + n_timesteps])  # 过去 n_timesteps 个时间步
            y.append(targets[i + n_timesteps:i + n_timesteps + n_future])  # 未来 n_future 个时间步
    # 转换为变长序列
    X = tf.ragged.constant(X)
    y = tf.ragged.constant(y)
    return X, y
# 设置参数
n_timesteps = 8  # 过去8个时间步 每6个小时
n_future = 2     # 预测未来2个时间步

# 构建时间序列
X, y = build_sequences(df, n_timesteps, n_future)

# 归一化（排除时间字段）
scaler = MinMaxScaler()
X_reshaped = X.reshape(-1, X.shape[-1])
X_reshaped[:, 1:] = scaler.fit_transform(X_reshaped[:, 1:])  # 只归一化特征字段（排除时间）
X = X_reshaped.reshape(X.shape)

y_reshaped = y.reshape(-1, y.shape[-1])
y_reshaped[:, 1:] = scaler.transform(y_reshaped[:, 1:])  # 只归一化目标字段（排除时间）
y = y_reshaped.reshape(y.shape)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


# 模型构建
n_features = 6  # 特征数量（时间、纬度、经度、等级、中心最低气压、2分钟平均风速）
model = Sequential([
    # CNN 层
    Conv1D(filters=64, kernel_size=3, activation="relu", input_shape=(n_timesteps, n_features)),
    MaxPooling1D(pool_size=2),
    Conv1D(filters=128, kernel_size=3, activation="relu"),
    MaxPooling1D(pool_size=2),

    # LSTM 层
    LSTM(128, return_sequences=True),
    LSTM(64),

    # 输出层
    Dense(n_future * n_features),  # 输出未来 n_future 个时间步的目标
    Reshape((n_future, n_features))  # 调整输出形状
])

# 编译模型
model.compile(optimizer="adam", loss="mse")

# 打印模型结构
model.summary()

# 模型训练
history = model.fit(
    X_train, y_train,
    epochs=50,
    batch_size=32,
    validation_data=(X_test, y_test))

# 模型评价
# 计算训练集和测试集上的误差
train_loss = model.evaluate(X_train, y_train, verbose=0)
test_loss = model.evaluate(X_test, y_test, verbose=0)

print(f"训练集误差 (MSE): {train_loss}")
print(f"测试集误差 (MSE): {test_loss}")



# 提取训练历史
train_mse = history.history["loss"]
val_mse = history.history["val_loss"]

# 绘制误差曲线
plt.figure(figsize=(10, 6))
plt.plot(train_mse, label="训练集误差 (MSE)")
plt.plot(val_mse, label="测试集误差 (MSE)")
plt.title("训练集和测试集误差随训练轮次的变化")
plt.xlabel("训练轮次")
plt.ylabel("均方误差 (MSE)")
plt.legend()
plt.grid(True)
plt.show()

