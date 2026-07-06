// Copyright (c) 2025，D-Robotics.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//视觉大模型解析器，基于llama.cpp实现
#include "include/post_process/llama_cpp_parser.h"

//1.构造函数，初始化模型参数，加载.gguf模型
LlamaCppParser::LlamaCppParser(const std::string& model_name, const std::string& system_prompt, const int n_threads) {
  common_init();
  params.model = model_name;
  params.cpuparams.n_threads = n_threads;
  params.sampling.temp = 0.5;
//加载LLaVA模型，返回模型指针
  model_ = CLI::llava_init(&params);
  if (model_ == NULL) {
      fprintf(stderr, "%s: error: failed to init llava model\n", __func__);
  }
}

//2.析构函数，释放模型资源
LlamaCppParser::~LlamaCppParser() {
  if (!ctx_llava_) {
    ctx_llava_->model = NULL;
    CLI::llava_free(ctx_llava_);
  }
  llama_model_free(model_);
}

//3.获取图像嵌入函数，从输入的张量中提取图像嵌入信息，返回一个包含嵌入数据和位置数量的结构体指针
struct llava_image_embed * LlamaCppParser::GetEmbedding(std::vector<std::shared_ptr<DNNTensor>> &tensors) {
  llava_image_embed * embed = (llava_image_embed*)malloc(sizeof(llava_image_embed)); //开辟图片特征结构体
  int num_tensors = 0;
  int length_tensors = 0;
  if (tensors[0]->properties.tensorLayout == HB_DNN_LAYOUT_NCHW) { //根据张量布局获取图像嵌入的维度信息
      num_tensors = tensors[0]->properties.alignedShape.dimensionSize[1];
      length_tensors = tensors[0]->properties.alignedShape.dimensionSize[2];
  } else {
      LOG_ERR("%s: failed to get embedding\n", __func__);
      exit(1);
  }

  hbSysFlushMem(&(tensors[0]->sysMem[0]), HB_SYS_MEM_CACHE_INVALIDATE);
  float *image_embed = reinterpret_cast<float *>(tensors[0]->sysMem[0].virAddr);

  embed->embed = image_embed; //把特征填到llava需要的结构里
  embed->n_image_pos = num_tensors;
  return embed; //返回给大模型使用
}

//4.接受图片特征+提问，让大模型生成回答
int32_t LlamaCppParser::Init(const std::string &system_prompt) {
  ctx_llava_ = CLI::llava_init_context(&params, model_);
  CLI::process_system_prompt(ctx_llava_, &params, system_prompt);
  return 0;
}

int32_t LlamaCppParser::Parse(
                const std::string &user_prompt, //用户提问文本
                std::vector<std::shared_ptr<DNNTensor>> &output_tensors, //输入的图片特征张量
                std::string &result, //输出的回答文本
                rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher, //ROS文本消息发布者，用于把回答发布到ROS话题
                int model_type) { //模型类型，0：InternVL2，1：SmolVLM2，不同模型的推理函数不同

  ggml_time_init();
  params.prompt = user_prompt;

  llava_image_embed * image_embed = GetEmbedding(output_tensors); //从输入的张量中提取图像嵌入信息，返回一个包含嵌入数据和位置数量的结构体指针

  if (!image_embed) {
      return -1;
  }

  // process the prompt
  if (model_type == 0) { //根据模型类型调用不同的推理函数，生成回答文本
    CLI::internvl2_process_prompt(ctx_llava_, image_embed, &params, params.prompt, result, publisher); 
  } else if (model_type == 1) {
    CLI::smolvlm2_process_prompt(ctx_llava_, image_embed, &params, params.prompt, result, publisher);
  } else {
    return -1;
  }

  llama_perf_context_print(ctx_llava_->ctx_llama);
  free(image_embed);

  ctx_llava_->model = NULL;
  CLI::llava_free(ctx_llava_);

  return 0;
}