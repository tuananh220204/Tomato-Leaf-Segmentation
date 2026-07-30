import torch
import torch.nn as nn
import torch.nn.functional as F


class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


class UNetPlusPlus(nn.Module):
    def __init__(self, in_channels: int = 3, out_channels: int = 1, base_channels: int = 32, depth: int = 5):
        super().__init__()
        self.depth = depth
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.channels = [base_channels * (2 ** level) for level in range(depth)]

        for row in range(depth):
            for col in range(depth - row):
                if col == 0:
                    in_ch = in_channels if row == 0 else self.channels[row - 1]
                else:
                    in_ch = self.channels[row] * col + self.channels[row + 1]
                setattr(self, f"conv{row}_{col}", ConvBlock(in_ch, self.channels[row]))

        self.final = nn.Conv2d(self.channels[0], out_channels, kernel_size=1)

    def _upsample_to(self, source, target):
        return F.interpolate(source, size=target.shape[2:], mode="bilinear", align_corners=False)

    def forward(self, x):
        nodes = {}

        nodes[(0, 0)] = self.conv0_0(x)
        for row in range(1, self.depth):
            block = getattr(self, f"conv{row}_0")
            nodes[(row, 0)] = block(self.pool(nodes[(row - 1, 0)]))

        for col in range(1, self.depth):
            for row in range(self.depth - col):
                block = getattr(self, f"conv{row}_{col}")
                inputs = [nodes[(row, prev_col)] for prev_col in range(col)]
                inputs.append(self._upsample_to(nodes[(row + 1, col - 1)], nodes[(row, col - 1)]))
                nodes[(row, col)] = block(torch.cat(inputs, dim=1))

        return self.final(nodes[(0, self.depth - 1)])


def build_unetplusplus_model(in_channels: int = 3, classes: int = 1, base_channels: int = 32):
    """Build the custom UNet++ architecture used by the saved checkpoint."""
    return UNetPlusPlus(in_channels=in_channels, out_channels=classes, base_channels=base_channels)
