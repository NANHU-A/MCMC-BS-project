"""
实验配置管理

使用YAML或JSON格式管理MCMC实验参数，便于实验复现和参数调整
"""

import yaml
import json
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum


class AlgorithmType(Enum):
    """算法类型枚举"""
    RWMH = "rwmh"
    MTM = "mtm"
    LB_MTM = "lb_mtm"
    ADAPTIVE_MTM = "adaptive_mtm"
    HMC = "hmc"
    PARALLEL = "parallel"


@dataclass
class ModelConfig:
    """模型配置"""
    model_type: str = "black_scholes"
    S0: float = 100.0  # 初始股价
    K: float = 100.0   # 行权价
    T: float = 1.0     # 到期时间
    r: float = 0.05    # 无风险利率
    sigma: float = 0.2 # 波动率
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class AlgorithmConfig:
    """算法配置"""
    algorithm_type: AlgorithmType = AlgorithmType.RWMH
    proposal_std: float = 0.3  # 提案标准差
    k_proposals: int = 4       # MTM的提案数量
    n_chains: int = 4          # 并行链数量
    tau: float = 1.0           # LB-MTM的温度参数
    batch_size: int = 100      # 批量处理大小
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        result = asdict(self)
        result['algorithm_type'] = self.algorithm_type.value
        return result


@dataclass
class ExperimentConfig:
    """实验配置"""
    name: str = "默认实验"
    description: str = ""
    model: ModelConfig = field(default_factory=ModelConfig)
    algorithm: AlgorithmConfig = field(default_factory=AlgorithmConfig)
    n_samples: int = 20000      # 总样本数
    burn_in: int = 5000         # 燃烧期
    n_repeats: int = 3          # 重复次数
    random_seed: int = 42       # 随机种子
    output_dir: str = "results" # 输出目录
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'name': self.name,
            'description': self.description,
            'model': self.model.to_dict(),
            'algorithm': self.algorithm.to_dict(),
            'n_samples': self.n_samples,
            'burn_in': self.burn_in,
            'n_repeats': self.n_repeats,
            'random_seed': self.random_seed,
            'output_dir': self.output_dir
        }
    
    def to_yaml(self, filepath: str):
        """保存为YAML文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)
    
    def to_json(self, filepath: str):
        """保存为JSON文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ExperimentConfig':
        """从字典创建配置"""
        # 处理算法类型
        if 'algorithm' in data and 'algorithm_type' in data['algorithm']:
            data['algorithm']['algorithm_type'] = AlgorithmType(data['algorithm']['algorithm_type'])
        
        # 创建配置对象
        model = ModelConfig(**data.get('model', {}))
        algorithm = AlgorithmConfig(**data.get('algorithm', {}))
        
        return cls(
            name=data.get('name', '默认实验'),
            description=data.get('description', ''),
            model=model,
            algorithm=algorithm,
            n_samples=data.get('n_samples', 20000),
            burn_in=data.get('burn_in', 5000),
            n_repeats=data.get('n_repeats', 3),
            random_seed=data.get('random_seed', 42),
            output_dir=data.get('output_dir', 'results')
        )
    
    @classmethod
    def from_yaml(cls, filepath: str) -> 'ExperimentConfig':
        """从YAML文件加载配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_json(cls, filepath: str) -> 'ExperimentConfig':
        """从JSON文件加载配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


# 预定义实验配置
def get_default_rwmh_config() -> ExperimentConfig:
    """获取默认RWMH配置"""
    return ExperimentConfig(
        name="RWMH基准测试",
        description="随机游走Metropolis-Hastings基准测试",
        algorithm=AlgorithmConfig(algorithm_type=AlgorithmType.RWMH)
    )


def get_mtm_comparison_configs() -> List[ExperimentConfig]:
    """获取MTM对比实验配置"""
    configs = []
    
    for k in [2, 4, 8, 16]:
        config = ExperimentConfig(
            name=f"MTM-K{k}测试",
            description=f"Multiple-Try Metropolis with K={k}",
            algorithm=AlgorithmConfig(
                algorithm_type=AlgorithmType.MTM,
                k_proposals=k
            )
        )
        configs.append(config)
    
    return configs


def get_adaptive_mtm_config() -> ExperimentConfig:
    """获取自适应MTM配置"""
    return ExperimentConfig(
        name="自适应MTM测试",
        description="自适应Multiple-Try Metropolis",
        algorithm=AlgorithmConfig(
            algorithm_type=AlgorithmType.ADAPTIVE_MTM,
            k_proposals=4
        )
    )


def get_parallel_config() -> ExperimentConfig:
    """获取并行MCMC配置"""
    return ExperimentConfig(
        name="并行MCMC测试",
        description="并行多链MCMC",
        algorithm=AlgorithmConfig(
            algorithm_type=AlgorithmType.PARALLEL,
            n_chains=4,
            k_proposals=4
        )
    )


def create_experiment_suite() -> Dict[str, ExperimentConfig]:
    """创建完整的实验套件"""
    suite = {
        "rwmh_baseline": get_default_rwmh_config(),
        "adaptive_mtm": get_adaptive_mtm_config(),
        "parallel_mcmc": get_parallel_config(),
    }
    
    # 添加MTM对比实验
    mtm_configs = get_mtm_comparison_configs()
    for i, config in enumerate(mtm_configs):
        suite[f"mtm_k{config.algorithm.k_proposals}"] = config
    
    return suite


def save_experiment_suite(suite: Dict[str, ExperimentConfig], base_dir: str = "configs"):
    """保存实验套件到文件"""
    import os
    os.makedirs(base_dir, exist_ok=True)
    
    for name, config in suite.items():
        yaml_path = os.path.join(base_dir, f"{name}.yaml")
        config.to_yaml(yaml_path)
        print(f"保存配置: {yaml_path}")


def load_experiment_suite(base_dir: str = "configs") -> Dict[str, ExperimentConfig]:
    """从文件加载实验套件"""
    import os
    suite = {}
    
    for filename in os.listdir(base_dir):
        if filename.endswith('.yaml') or filename.endswith('.yml'):
            filepath = os.path.join(base_dir, filename)
            name = os.path.splitext(filename)[0]
            config = ExperimentConfig.from_yaml(filepath)
            suite[name] = config
    
    return suite


# 示例使用
def example_usage():
    """配置模块使用示例"""
    print("配置管理模块示例")
    print("=" * 60)
    
    # 创建默认配置
    config = get_default_rwmh_config()
    print(f"实验名称: {config.name}")
    print(f"样本数量: {config.n_samples}")
    print(f"算法类型: {config.algorithm.algorithm_type.value}")
    print(f"提案标准差: {config.algorithm.proposal_std}")
    
    # 转换为字典
    config_dict = config.to_dict()
    print(f"\n配置字典: {json.dumps(config_dict, indent=2, ensure_ascii=False)[:200]}...")
    
    # 创建实验套件
    suite = create_experiment_suite()
    print(f"\n实验套件包含 {len(suite)} 个实验:")
    for name in suite.keys():
        print(f"  - {name}")
    
    # 保存配置示例
    print("\n保存配置到文件...")
    try:
        config.to_yaml("example_config.yaml")
        print("YAML文件保存成功")
        
        config.to_json("example_config.json")
        print("JSON文件保存成功")
    except Exception as e:
        print(f"保存失败: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    example_usage()