import os
import random

import torch

from TransformerTTS.TransformerTTS import Transformer
from TransformerTTS.TransformerTTSDataset import TransformerTTSDataset
from TransformerTTS.transformer_tts_train_loop import train_loop
from Utility.path_to_transcript_dicts import build_path_to_transcript_dict_ljspeech as build_path_to_transcript_dict


def run(gpu_id, resume_checkpoint, finetune, model_dir):
    if gpu_id == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        device = torch.device("cpu")

    else:
        os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        os.environ["CUDA_VISIBLE_DEVICES"] = "{}".format(gpu_id)
        device = torch.device("cuda")

    torch.manual_seed(13)
    random.seed(13)

    print("Preparing")
    cache_dir = os.path.join("Corpora", "LJSpeech")
    if model_dir is not None:
        save_dir = model_dir
    else:
        save_dir = os.path.join("Models", "TransformerTTS_SingleHead")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    path_to_transcript_dict = build_path_to_transcript_dict()

    train_set = TransformerTTSDataset(path_to_transcript_dict,
                                      cache_dir=cache_dir,
                                      lang="en",
                                      min_len_in_seconds=1,
                                      max_len_in_seconds=10,
                                      rebuild_cache=False)

    model = Transformer(idim=166,
                        odim=80,
                        spk_embed_dim=None,
                        num_heads_applied_guided_attn=-1,
                        aheads=1,
                        guided_attn_loss_lambda=10.0,
                        dlayers=1,
                        num_layers_applied_guided_attn=-1,
                        adim=256)

    print(sum(p.numel() for p in model.parameters() if p.requires_grad))

    print("Training model")
    train_loop(net=model,
               train_dataset=train_set,
               device=device,
               save_directory=save_dir,
               steps=300000,
               batch_size=64,
               gradient_accumulation=1,
               epochs_per_save=10,
               use_speaker_embedding=False,
               lang="en",
               lr=0.02,
               warmup_steps=8000,
               path_to_checkpoint=resume_checkpoint,
               fine_tune=finetune)