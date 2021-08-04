import multiprocessing
import os
import random
from tqdm import tqdm

import multiprocessing as mp
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset


class PDFConv(nn.Module):
    def __init__(self):
        super(PDFConv, self).__init__()
        self.embedding = nn.Embedding(num_embeddings=256, embedding_dim=8)
        self.conv1 = nn.Sequential(
            nn.Conv1d(8, 128, kernel_size=11),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=7),
            nn.Conv1d(128, 128, kernel_size=7),
            nn.ReLU()
        )

        self.conv2 = nn.Sequential(
            nn.Conv1d(8, 128, kernel_size=11),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=7),
            nn.Conv1d(128, 128, kernel_size=7),
            nn.Sigmoid()
        )

        self.classifier = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Softmax()
        )

    def forward(self, x):
        x = self.embedding(x)
        x1 = self.conv1(x)
        x2 = self.conv2(x)
        x = torch.matmul(x1, x2)
        x, _ = torch.max(x, 1)
        out = self.classifier(x)
        return out


class PDFDataset(Dataset):
    def __init__(self, amount=200000):
        super(PDFDataset, self).__init__()
        self.dataset = []
        self.labels = []
        self.amount = amount

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.dataset[idx], self.labels[idx]

    def __process__(self, file_path):
        with open(file_path, 'rb') as f:
            food = f.read(self.amount)
            food = list(food)
            food.extend(0 for _ in range(200000 - len(food)))
            return food

    def add_files(self, file_paths, label):
        print("Loading Files...")
        for path in tqdm(file_paths):
            food = self.__process__(path)
            self.dataset.append(food)
            self.labels.append(label)


def train(model: nn.Module, dataset, batch_size, epoch):
    criterion = torch.nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters())

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model.to(device)
    criterion.to(device)
    train_dataloader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=True)

    model.train()
    for e in range(epoch):
        with tqdm(train_dataloader) as t:
            for data, label in t:
                data = data.to(device)
                label = label.to(device)
                prediction = model(data)
                loss = criterion(prediction, label)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                t.set_postfix(epoch=f"{e + 1} of {epoch}", loss=f"{loss.item():.4f}")
        with open(f"sick_{e}.pt", 'wb') as f:
            torch.save(model, f)


def evaluate(model, dataset, batch_size):
    test_dataloader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=False)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    model.to(device)
    model.eval()
    with torch.no_grad():
        with tqdm(test_dataloader) as t:
            for data, label in t:
                data = data.to(device)
                label = label.to(device)
                prediction = model(data)


def main():
    mal_paths = []
    ben_paths = []
    for path, _, files in os.walk(r'D:\Source\pdf\Benign_PDF'):
        for file in files:
            if os.extsep in file:
                name, ext = file.rsplit(os.extsep, maxsplit=1)
            else:
                name, ext = file, "file",
            if ext == 'pdf' or ext == "file":
                ben_paths.append(path + os.sep + file)
    for path, _, files in os.walk(r'D:\Source\pdf\Malicious_PDF'):
        for file in files:
            if os.extsep in file:
                name, ext = file.rsplit(os.extsep, maxsplit=1)
            else:
                name, ext = file, "file",
            if ext == 'pdf' or ext == "file":
                mal_paths.append(path + os.sep + file)
    random.shuffle(mal_paths)
    random.shuffle(ben_paths)
    train_mal, test_mal = mal_paths[:int(len(mal_paths) * 0.75)], mal_paths[int(len(mal_paths) * 0.75):]
    train_ben, test_ben = ben_paths[:int(len(ben_paths) * 0.75)], ben_paths[int(len(ben_paths) * 0.75):]
    train_dataset = PDFDataset()
    train_dataset.add_files(train_mal, 1)
    train_dataset.add_files(train_ben, 0)

    model = PDFConv()
    train(model, train_dataset, batch_size=1024, epoch=32)


if __name__ == '__main__':
    main()
