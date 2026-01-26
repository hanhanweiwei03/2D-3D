from ultralytics import YOLO
import os
import argparse
import yaml
import torch

def parse_args():
    parser = argparse.ArgumentParser()
    # 核心参数（默认device改为cpu，适配无GPU环境）
    parser.add_argument("--yaml_path", type=str, default="./data.yaml", help="data.yaml路径")
    parser.add_argument("--model", type=str, default="yolov11n.pt", help="基础模型")
    parser.add_argument("--epochs", type=int, default=40, help="训练轮次")
    parser.add_argument("--batch", type=int, default=4, help="CPU批次调小至4，避免内存不足")
    parser.add_argument("--device", type=str, default="cpu", help="强制CPU（无GPU环境）")
    parser.add_argument("--export_format", type=str, default="pt", help="导出格式(pt/onnx)")
    return parser.parse_args()

def main(args):
    # 2. 加载模型
    model = YOLO(args.model)
    print(f"✅ 加载模型: {args.model}")

    # 3. 训练（CPU适配：调小batch，关闭mixup减少计算）
    print("\n🚀 开始CPU训练...")
    train_results = model.train(
        data=args.yaml_path,
        epochs=args.epochs,
        batch=args.batch,
        device=args.device,
        imgsz=640,
        patience=10,
        save=True,
        val=True,
        plots=True,
        mixup=0,  # CPU环境关闭mixup，加速训练
        multi_scale = True,  # 开启多尺度训练（0.8~1.2倍）
        scale = 0.9,  # 缩放增强幅度拉满（±90%，0.1~1.9倍）
        perspective = 0.0,  # 关闭透视变换（仅保留纯缩放）
    )

    # 4. test数据集评估
    with open(args.yaml_path, "r") as f:
        yaml_data = yaml.safe_load(f)
    if "test" in yaml_data and os.path.exists(yaml_data["test"]):
        print("\n📊 开始test评估...")
        test_results = model.val(data=args.yaml_path, split="test", device=args.device, imgsz=640)
        print("\n✅ Test核心指标:")
        print(f"mAP50: {test_results.results_dict['metrics/mAP50(B)']:.4f}")
        print(f"Precision: {test_results.results_dict['metrics/precision(B)']:.4f}")
    else:
        print("\n⚠️ 未配置test路径，跳过评估")

    # 5. 导出权重
    best_model_path = os.path.join(model.trainer.save_dir, "weights", "best.pt")
    print(f"best.pt path is: {best_model_path}")

    # 6. 结果汇总
    print(f"\n🎉 流程结束!")
    print(f"最佳模型: {best_model_path}")
    print(f"训练日志: {model.trainer.save_dir}")

if __name__ == "__main__":
    args = parse_args()
    main(args)